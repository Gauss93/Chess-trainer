"""Application Flask du projet Chess Trainer.

Ce module configure l'application, la session utilisateur, les interactions
avec la base de donnees et un chrono de 10 minutes par joueur.
"""

import logging
import os
from datetime import datetime, timezone

from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from chess_logic import (
    board_from_fen,
    create_board,
    get_fen,
    make_move,
    make_random_ai_move,
)
from extensions import db
from models import Game

TIME_CONTROL_MINUTES = 10
TIME_CONTROL_SECONDS = TIME_CONTROL_MINUTES * 60

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_environment() -> bool:
    """Charge les variables d'environnement depuis `.env`.

    Returns:
        bool: `True` si un fichier `.env` a ete trouve et charge, sinon `False`.
    """

    dotenv_path = find_dotenv(usecwd=True)
    if not dotenv_path:
        logger.warning(
            "Aucun fichier .env trouve. Les variables d'environnement "
            "systeme et les valeurs par defaut seront utilisees."
        )
        return False

    load_dotenv(dotenv_path)
    logger.info("Configuration chargee depuis %s.", dotenv_path)
    return True


def build_database_url() -> str:
    """Construit l'URL de connexion SQLAlchemy.

    La priorite est donnee a `DATABASE_URL`. Si elle est absente,
    l'application bascule sur SQLite pour conserver un mode de secours local.

    Returns:
        str: URL SQLAlchemy prete a etre injectee dans la configuration Flask.
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(basedir, "instance", "chess.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        database_url = f"sqlite:///{db_path}"
        logger.warning(
            "DATABASE_URL absente. Utilisation du fallback SQLite sur %s.",
            db_path,
        )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("Schema postgres:// converti en postgresql:// pour SQLAlchemy.")

    return database_url


def utc_now() -> datetime:
    """Retourne un horodatage UTC conscient du fuseau.

    Returns:
        datetime: Date/heure UTC utilisee pour le chrono serveur.
    """

    return datetime.now(timezone.utc)


def normalize_utc_datetime(value: datetime | None) -> datetime | None:
    """Normalise une date SQLAlchemy vers un datetime UTC coherent.

    Certaines bases ou drivers retournent un `datetime` sans information de
    fuseau. Le chrono manipule toujours des dates UTC timezone-aware pour
    eviter les erreurs de soustraction entre datetimes incompatibles.

    Args:
        value (datetime | None): Valeur lue depuis la base.

    Returns:
        datetime | None: Valeur UTC timezone-aware ou `None`.
    """

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def commit_session(context: str) -> bool:
    """Valide la transaction SQLAlchemy en securisant les erreurs reseau/DB.

    En cas d'echec, la session SQLAlchemy est annulee avec `rollback()` afin
    d'eviter qu'une transaction invalide ne casse les requetes suivantes.

    Args:
        context (str): Description courte de l'operation en cours pour le log.

    Returns:
        bool: `True` si le commit a reussi, sinon `False`.
    """

    try:
        db.session.commit()
        return True
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Echec du commit SQLAlchemy pendant %s.", context)
        return False


def ensure_game_timer_columns() -> None:
    """Ajoute les colonnes de chrono si la table `game` existe deja sans elles.

    Cette mise a niveau simple evite d'imposer Alembic pour ce projet de demo.
    Elle ne remplace pas une vraie strategie de migration sur un projet plus
    long terme.
    """

    inspector = inspect(db.engine)
    if "game" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("game")}
    required_columns = {
        "white_time_left": (
            "ALTER TABLE game ADD COLUMN white_time_left INTEGER NOT NULL DEFAULT 600"
        ),
        "black_time_left": (
            "ALTER TABLE game ADD COLUMN black_time_left INTEGER NOT NULL DEFAULT 600"
        ),
        "last_move_at": "ALTER TABLE game ADD COLUMN last_move_at TIMESTAMP",
        "time_control_minutes": (
            "ALTER TABLE game ADD COLUMN time_control_minutes INTEGER NOT NULL DEFAULT 10"
        ),
    }

    for column_name, ddl in required_columns.items():
        if column_name in existing_columns:
            continue

        logger.info("Ajout de la colonne manquante `%s` sur la table game.", column_name)
        db.session.execute(text(ddl))

    db.session.commit()


def get_active_color(board) -> str:
    """Retourne la couleur qui doit jouer pour le FEN courant.

    Args:
        board (chess.Board): Plateau reconstruit depuis le FEN stocke.

    Returns:
        str: `white` si les blancs ont le trait, sinon `black`.
    """

    return "white" if board.turn else "black"


def apply_clock(game: Game, board, now: datetime | None = None) -> tuple[bool, str | None]:
    """Met a jour les temps restants selon le trait courant.

    Le serveur fait foi pour le chrono. Le temps ecoule depuis `last_move_at`
    est retire au joueur qui devait jouer avant de traiter la prochaine action.

    Args:
        game (Game): Partie persistante dont les temps doivent etre recalcules.
        board (chess.Board): Plateau associe permettant d'identifier le trait.
        now (datetime | None): Horodatage de reference, principalement utile
            pour les tests. `utc_now()` est utilise si absent.

    Returns:
        tuple[bool, str | None]: Tuple indiquant si une pendule est tombee et,
        si oui, la couleur en defaite au temps.
    """

    now = now or utc_now()
    if game.is_finished:
        return False, None

    game.last_move_at = normalize_utc_datetime(game.last_move_at)

    if game.last_move_at is None:
        game.last_move_at = now
        return False, None

    elapsed_seconds = int((now - game.last_move_at).total_seconds())
    if elapsed_seconds <= 0:
        return False, None

    active_color = get_active_color(board)
    if active_color == "white":
        game.white_time_left = max(0, game.white_time_left - elapsed_seconds)
        if game.white_time_left == 0:
            game.is_finished = True
            game.result = "black_time_win"
            game.last_move_at = now
            return True, "white"
    else:
        game.black_time_left = max(0, game.black_time_left - elapsed_seconds)
        if game.black_time_left == 0:
            game.is_finished = True
            game.result = "white_time_win"
            game.last_move_at = now
            return True, "black"

    game.last_move_at = now
    return False, None


def clock_payload(game: Game, board) -> dict:
    """Construit l'etat du chrono pour le front.

    Args:
        game (Game): Partie persistante contenant les temps restants.
        board (chess.Board): Plateau courant pour identifier le trait actif.

    Returns:
        dict: Donnees compactes utilisees par le template et le JavaScript.
    """

    return {
        "white_time_left": game.white_time_left,
        "black_time_left": game.black_time_left,
        "active_color": None if game.is_finished else get_active_color(board),
        "time_control_minutes": game.time_control_minutes,
        "is_finished": game.is_finished,
        "result": game.result,
    }


load_environment()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = build_database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        ensure_game_timer_columns()
    except SQLAlchemyError:
        logger.exception("Impossible d'initialiser la base de donnees avec create_all().")


@app.route("/")
def welcome():
    """Redirige l'utilisateur vers la partie active ou en cree une nouvelle.

    La session Flask conserve le `game_id` et le FEN de la derniere partie
    recuperee afin de reconnecter l'utilisateur a son etat de jeu.

    Returns:
        Response: Redirection vers `/board` ou `/new-game`.
    """

    try:
        last_game = Game.query.order_by(Game.created_at.desc()).first()
    except SQLAlchemyError:
        logger.exception("Lecture de la derniere partie impossible.")
        return redirect("/new-game")

    if last_game:
        session["game_id"] = last_game.id
        session["fen"] = last_game.fen
        return redirect("/board")

    return redirect("/new-game")


@app.route("/new-game")
def new_game():
    """Initialise une nouvelle partie avec un chrono de 10 minutes.

    La session Flask stocke l'identifiant de la partie, la couleur choisie et
    le FEN courant. La base persiste egalement les deux pendules afin que le
    temps restant survive a un rafraichissement de page.

    Returns:
        Response: Redirection vers l'echiquier si la sauvegarde reussit.
        tuple[str, int]: Message d'erreur HTTP 503 si la base est indisponible.
    """

    color = request.args.get("color", "white")
    board = create_board()

    if color == "black":
        make_random_ai_move(board)

    now = utc_now()
    fen = get_fen(board)
    game = Game(
        fen=fen,
        white_time_left=TIME_CONTROL_SECONDS,
        black_time_left=TIME_CONTROL_SECONDS,
        last_move_at=now,
        time_control_minutes=TIME_CONTROL_MINUTES,
    )
    db.session.add(game)

    if not commit_session("la creation d'une nouvelle partie avec chrono"):
        return "Database unavailable while creating a new game.", 503

    session["game_id"] = game.id
    session["fen"] = fen
    session["color"] = color

    return redirect("/board")


@app.route("/play", methods=["POST"])
def play():
    """Traite un coup joueur, le chrono, puis sauvegarde le nouvel etat.

    Avant de jouer le coup, le serveur debite le temps du joueur au trait
    depuis `last_move_at`. Si son temps est ecoule, la partie est arretee
    avant toute modification supplementaire.

    Returns:
        Response: Reponse JSON contenant l'etat de la partie ou une erreur HTTP.
    """

    game_id = session.get("game_id")
    if not game_id or "fen" not in session:
        return jsonify({"error": "No active game"}), 400

    data = request.get_json(silent=True) or {}
    move_uci = data.get("move")
    if not move_uci:
        return jsonify({"error": "Missing move"}), 400

    try:
        game = db.session.get(Game, game_id)
    except SQLAlchemyError:
        logger.exception("Lecture de la partie %s impossible.", game_id)
        return jsonify({"error": "Database unavailable"}), 503

    if not game:
        return jsonify({"error": "Game not found"}), 404

    board = board_from_fen(session["fen"])

    if game.is_finished:
        return jsonify({"error": "Game already finished", "clock": clock_payload(game, board)}), 400

    flag_fell, loser = apply_clock(game, board)
    if flag_fell:
        session["fen"] = game.fen
        if not commit_session("la cloture d'une partie au temps"):
            return jsonify({"error": "Database unavailable"}), 503
        return (
            jsonify(
                {
                    "error": f"{loser} ran out of time",
                    "game_over": True,
                    "clock": clock_payload(game, board),
                }
            ),
            400,
        )

    if not make_move(board, move_uci):
        return jsonify({"error": "Illegal move"}), 400

    ai_move = make_random_ai_move(board)
    new_fen = get_fen(board)

    game.fen = new_fen
    game.last_move_at = utc_now()

    if board.is_game_over():
        game.is_finished = True
        game.result = "board_game_over"

    if not commit_session("la mise a jour d'une partie via /play avec chrono"):
        return jsonify({"error": "Database unavailable"}), 503

    session["fen"] = new_fen

    return jsonify(
        {
            "player_move": move_uci,
            "ai_move": ai_move,
            "fen": new_fen,
            "ascii": str(board),
            "game_over": board.is_game_over() or game.is_finished,
            "clock": clock_payload(game, board),
        }
    )


@app.route("/board")
def board():
    """Affiche l'echiquier et les pendules a partir de l'etat en session.

    La vue lit le FEN depuis la session puis recharge la partie SQL pour
    afficher des temps a jour. Le chrono est recalcule serveur avant rendu.

    Returns:
        Response | str: Template HTML de l'echiquier ou message d'erreur.
    """

    game_id = session.get("game_id")
    if not game_id or "fen" not in session:
        return "Pas de partie commencee."

    try:
        game = db.session.get(Game, game_id)
    except SQLAlchemyError:
        logger.exception("Lecture de la partie %s impossible pour /board.", game_id)
        return "Database unavailable", 503

    if not game:
        return "Partie introuvable.", 404

    board_state = board_from_fen(session["fen"])
    apply_clock(game, board_state)
    if not commit_session("la mise a jour du chrono lors de l'affichage du board"):
        return "Database unavailable", 503

    color = session.get("color", "white")
    return render_template(
        "board.html",
        fen=session["fen"],
        color=color,
        clock=clock_payload(game, board_state),
    )


@app.route("/play-form", methods=["POST"])
def play_form():
    """Traite un coup joueur depuis un formulaire HTML standard.

    Comme la route JSON `/play`, cette route debite d'abord le chrono du joueur
    au trait, applique les coups, puis persiste le nouvel etat en base.

    Returns:
        Response | str: Redirection vers l'echiquier ou message d'erreur.
    """

    game_id = session.get("game_id")
    if not game_id or "fen" not in session:
        return "No active game", 400

    move_uci = request.form.get("move")
    if not move_uci:
        return "Missing move", 400

    try:
        game = db.session.get(Game, game_id)
    except SQLAlchemyError:
        logger.exception("Lecture de la partie %s impossible via /play-form.", game_id)
        return "Database unavailable", 503

    if not game:
        return "Game not found", 404

    board_state = board_from_fen(session["fen"])
    if game.is_finished:
        return "Game already finished", 400

    flag_fell, loser = apply_clock(game, board_state)
    if flag_fell:
        if not commit_session("la cloture d'une partie au temps via /play-form"):
            return "Database unavailable", 503
        return f"{loser} ran out of time", 400

    if not make_move(board_state, move_uci):
        return "Illegal move", 400

    make_random_ai_move(board_state)
    new_fen = get_fen(board_state)

    game.fen = new_fen
    game.last_move_at = utc_now()

    if board_state.is_game_over():
        game.is_finished = True
        game.result = "board_game_over"

    if not commit_session("la mise a jour d'une partie via /play-form avec chrono"):
        return "Database unavailable", 503

    session["fen"] = new_fen
    return redirect("/board")


@app.route("/debug-db")
def debug_db():
    """Expose les parties en base pour le diagnostic de developpement.

    Cette route lit la table `Game` pour verifier le contenu persiste, y
    compris les temps restants du chrono.

    Returns:
        Response: Liste JSON des parties ou erreur HTTP 503 si la base echoue.
    """

    try:
        games = Game.query.all()
    except SQLAlchemyError:
        logger.exception("Lecture de debug de la base impossible.")
        return jsonify({"error": "Database unavailable"}), 503

    return jsonify(
        [
            {
                "id": game.id,
                "fen": game.fen,
                "white_time_left": game.white_time_left,
                "black_time_left": game.black_time_left,
                "is_finished": game.is_finished,
                "result": game.result,
            }
            for game in games
        ]
    )


if __name__ == "__main__":
    logger.info("Demarrage du serveur Flask sur http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
