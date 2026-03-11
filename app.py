"""Application Flask du projet Chess Trainer.

Ce module configure l'application, la session utilisateur et les
interactions avec la base de donnees pour persister l'etat des parties.
"""

import logging
import os

from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session
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


load_environment()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = build_database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
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
    game = Game(fen=fen)
    db.session.add(game)

    if not commit_session("la creation d'une nouvelle partie"):
        return "Database unavailable while creating a new game.", 503

    session["game_id"] = game.id
    session["fen"] = fen
    session["color"] = color

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

    board = board_from_fen(session["fen"])
    if not make_move(board, move_uci):
        return jsonify({"error": "Illegal move"}), 400

    ai_move = make_random_ai_move(board)
    new_fen = get_fen(board)

    try:
        game = db.session.get(Game, game_id)
    except SQLAlchemyError:
        logger.exception("Lecture de la partie %s impossible.", game_id)
        return jsonify({"error": "Database unavailable"}), 503

    if game:
        game.fen = new_fen
        if not commit_session("la mise a jour d'une partie via /play"):
            return jsonify({"error": "Database unavailable"}), 503

    session["fen"] = new_fen

    return jsonify(
        {
            "player_move": move_uci,
            "ai_move": ai_move,
            "fen": new_fen,
            "ascii": str(board),
            "game_over": board.is_game_over(),
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

    color = session.get("color", "white")
    return render_template("board.html", fen=session["fen"], color=color)


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

    if game:
        game.fen = new_fen
        if not commit_session("la mise a jour d'une partie via /play-form"):
            return "Database unavailable", 503

    session["fen"] = new_fen
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
