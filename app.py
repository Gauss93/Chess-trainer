"""Application Flask du projet Chess Trainer.

Ce module configure l'application, la session utilisateur et les
interactions avec la base de donnees pour persister l'etat des parties.
"""

import logging
import os
import time

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

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


DEFAULT_CLOCK = {
    "white_time_left": 600,
    "black_time_left": 600,
    "active_color": "white",
    "is_finished": False,
    "result": None,
}


def build_initial_clock(active_color: str = "white") -> dict:
    """Construit un chrono initial avec horodatage serveur."""

    return {
        **DEFAULT_CLOCK,
        "active_color": active_color,
        "last_updated_at": time.time(),
    }


def build_clock_from_game(game: Game | None, fallback_color: str = "white") -> dict:
    """Construit un chrono a partir des donnees persistees en base."""

    if not game:
        return build_initial_clock(active_color=fallback_color)

    active_color = game.active_color
    if active_color not in {"white", "black"}:
        active_color = None

    return {
        "white_time_left": game.white_time_left
        if game.white_time_left is not None
        else DEFAULT_CLOCK["white_time_left"],
        "black_time_left": game.black_time_left
        if game.black_time_left is not None
        else DEFAULT_CLOCK["black_time_left"],
        "active_color": active_color,
        "is_finished": bool(game.is_finished),
        "result": game.result,
        "last_updated_at": game.clock_last_updated_at or time.time(),
    }


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


def sync_clock_state(clock: dict | None = None) -> dict:
    """Met a jour le chrono selon le temps reel ecoule cote serveur."""

    current_clock = dict(clock or session.get("clock") or build_initial_clock())
    now = time.time()

    if current_clock.get("is_finished") or not current_clock.get("active_color"):
        current_clock["last_updated_at"] = now
        return current_clock

    last_updated_at = float(current_clock.get("last_updated_at", now))
    elapsed_seconds = max(0, int(now - last_updated_at))

    if elapsed_seconds > 0:
        active_color = current_clock["active_color"]
        time_key = f"{active_color}_time_left"
        current_clock[time_key] = max(
            0,
            int(current_clock.get(time_key, DEFAULT_CLOCK[time_key])) - elapsed_seconds,
        )

        if current_clock[time_key] == 0:
            current_clock["is_finished"] = True
            current_clock["result"] = (
                "black_time_win" if active_color == "white" else "white_time_win"
            )
            current_clock["active_color"] = None

    current_clock["last_updated_at"] = now
    return current_clock


def get_clock_state() -> dict:
    """Retourne le chrono courant et le resynchronise dans la session."""

    clock = sync_clock_state()
    session["clock"] = clock
    return clock


def persist_clock_to_game(game: Game, clock: dict) -> None:
    """Copie l'etat du chrono courant dans le modele SQLAlchemy."""

    game.white_time_left = int(clock["white_time_left"])
    game.black_time_left = int(clock["black_time_left"])
    game.active_color = clock.get("active_color")
    game.clock_last_updated_at = float(clock["last_updated_at"])
    game.is_finished = bool(clock.get("is_finished"))
    game.result = clock.get("result")


def load_game_into_session(game: Game) -> None:
    """Recharge la partie et son chrono depuis la base vers la session."""

    session["game_id"] = game.id
    session["fen"] = game.fen
    session["color"] = game.player_color or "white"
    session["clock"] = build_clock_from_game(game, fallback_color=session["color"])


def ensure_game_schema() -> None:
    """Ajoute les colonnes manquantes pour les parties existantes."""

    inspector = inspect(db.engine)
    existing_columns = {column["name"] for column in inspector.get_columns("game")}
    missing_columns = {
        "player_color": "ALTER TABLE game ADD COLUMN player_color VARCHAR(5)",
        "white_time_left": "ALTER TABLE game ADD COLUMN white_time_left INTEGER",
        "black_time_left": "ALTER TABLE game ADD COLUMN black_time_left INTEGER",
        "active_color": "ALTER TABLE game ADD COLUMN active_color VARCHAR(5)",
        "clock_last_updated_at": "ALTER TABLE game ADD COLUMN clock_last_updated_at FLOAT",
    }

    with db.engine.begin() as connection:
        for column_name, ddl in missing_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(ddl))

        connection.execute(
            text("UPDATE game SET player_color = COALESCE(player_color, 'white')")
        )
        connection.execute(
            text("UPDATE game SET white_time_left = COALESCE(white_time_left, 600)")
        )
        connection.execute(
            text("UPDATE game SET black_time_left = COALESCE(black_time_left, 600)")
        )
        connection.execute(
            text("UPDATE game SET active_color = COALESCE(active_color, 'white')")
        )
        connection.execute(
            text(
                "UPDATE game SET clock_last_updated_at = "
                "COALESCE(clock_last_updated_at, :timestamp)"
            ),
            {"timestamp": time.time()},
        )


load_environment()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = build_database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        ensure_game_schema()
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
        load_game_into_session(last_game)
        return redirect("/board")

    return redirect("/new-game")


@app.route("/new-game")
def new_game():
    """Initialise une nouvelle partie et la persiste en base.

    La session Flask stocke l'identifiant de la partie, la couleur choisie et
    le FEN courant. La base sert de persistance durable pour restaurer une
    partie apres redemarrage ou perte de session navigateur.

    Returns:
        Response: Redirection vers l'echiquier si la sauvegarde reussit.
        tuple[str, int]: Message d'erreur HTTP 503 si la base est indisponible.
    """

    color = request.args.get("color", "white")
    board = create_board()

    if color == "black":
        make_random_ai_move(board)

    fen = get_fen(board)
    initial_clock = build_initial_clock(active_color=color)
    game = Game(fen=fen, player_color=color)
    persist_clock_to_game(game, initial_clock)
    db.session.add(game)

    if not commit_session("la creation d'une nouvelle partie"):
        return "Database unavailable while creating a new game.", 503

    session["game_id"] = game.id
    session["fen"] = fen
    session["color"] = color
    session["clock"] = initial_clock

    return redirect("/board")


@app.route("/play", methods=["POST"])
def play():
    """Traite un coup joueur via l'API JSON puis sauvegarde le nouvel etat.

    La session Flask fournit le `game_id` et le FEN courant. Une fois le coup
    valide et la reponse IA jouee, le nouvel etat est enregistre en base pour
    garder la session web et la persistence SQL synchronisees.

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

    clock = get_clock_state()
    if clock["is_finished"]:
        return jsonify({"error": "Game is already finished", "clock": clock}), 400

    board = board_from_fen(session["fen"])
    if not make_move(board, move_uci):
        return jsonify({"error": "Illegal move", "clock": clock}), 400

    ai_move = make_random_ai_move(board)
    new_fen = get_fen(board)

    try:
        game = db.session.get(Game, game_id)
    except SQLAlchemyError:
        logger.exception("Lecture de la partie %s impossible.", game_id)
        return jsonify({"error": "Database unavailable"}), 503

    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game:
        game.fen = new_fen
        persist_clock_to_game(game, clock)
        if not commit_session("la mise a jour d'une partie via /play"):
            return jsonify({"error": "Database unavailable"}), 503

    session["fen"] = new_fen
    clock = sync_clock_state(session.get("clock"))

    if board.is_game_over():
        clock["is_finished"] = True
        clock["result"] = "board_game_over"
        clock["active_color"] = None

    clock["last_updated_at"] = time.time()
    session["clock"] = clock
    persist_clock_to_game(game, clock)

    if not commit_session("la sauvegarde du chrono via /play"):
        return jsonify({"error": "Database unavailable"}), 503

    return jsonify(
        {
            "player_move": move_uci,
            "ai_move": ai_move,
            "fen": new_fen,
            "ascii": str(board),
            "game_over": board.is_game_over(),
            "clock": clock,
        }
    )


@app.route("/board")
def board():
    """Affiche l'echiquier a partir de l'etat stocke en session.

    La vue lit le FEN et la couleur depuis la session Flask. Aucun acces en
    base n'est necessaire ici tant que l'etat de la partie est deja charge.

    Returns:
        Response | str: Template HTML de l'echiquier ou message si aucune
        partie n'est disponible dans la session.
    """

    if "fen" not in session:
        return "Pas de partie commencee."

    game_id = session.get("game_id")

    if game_id:
        try:
            game = db.session.get(Game, game_id)
        except SQLAlchemyError:
            logger.exception("Lecture de la partie %s impossible via /board.", game_id)
            game = None
        if game:
            load_game_into_session(game)

    color = session.get("color", "white")
    session.setdefault("clock", build_initial_clock(active_color=color))
    return render_template(
        "board.html",
        fen=session["fen"],
        color=color,
        clock=get_clock_state(),
    )


@app.route("/play-form", methods=["POST"])
def play_form():
    """Traite un coup joueur depuis un formulaire HTML standard.

    Comme la route JSON `/play`, cette route relit le FEN depuis la session,
    applique les coups, puis persiste le nouvel etat en base pour garder la
    partie recuperable au prochain chargement.

    Returns:
        Response | str: Redirection vers l'echiquier ou message d'erreur.
    """

    game_id = session.get("game_id")
    if not game_id or "fen" not in session:
        return "No active game", 400

    move_uci = request.form.get("move")
    if not move_uci:
        return "Missing move", 400

    clock = get_clock_state()
    if clock["is_finished"]:
        return "Game is already finished", 400

    board = board_from_fen(session["fen"])
    if not make_move(board, move_uci):
        return "Illegal move", 400

    make_random_ai_move(board)
    new_fen = get_fen(board)

    try:
        game = db.session.get(Game, game_id)
    except SQLAlchemyError:
        logger.exception("Lecture de la partie %s impossible via /play-form.", game_id)
        return "Database unavailable", 503

    if not game:
        return "Game not found", 404

    if game:
        game.fen = new_fen
        persist_clock_to_game(game, clock)
        if not commit_session("la mise a jour d'une partie via /play-form"):
            return "Database unavailable", 503

    session["fen"] = new_fen
    clock = sync_clock_state(session.get("clock"))

    if board.is_game_over():
        clock["is_finished"] = True
        clock["result"] = "board_game_over"
        clock["active_color"] = None

    clock["last_updated_at"] = time.time()
    session["clock"] = clock
    persist_clock_to_game(game, clock)
    if not commit_session("la sauvegarde du chrono via /play-form"):
        return "Database unavailable", 503
    return redirect("/board")


@app.route("/debug-db")
def debug_db():
    """Expose les parties en base pour le diagnostic de developpement.

    Cette route lit la table `Game` pour verifier le contenu persiste. Elle ne
    modifie ni la session Flask ni les donnees SQL.

    Returns:
        Response: Liste JSON des parties ou erreur HTTP 503 si la base echoue.
    """

    try:
        games = Game.query.all()
    except SQLAlchemyError:
        logger.exception("Lecture de debug de la base impossible.")
        return jsonify({"error": "Database unavailable"}), 503

    return jsonify([{"id": game.id, "fen": game.fen} for game in games])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
