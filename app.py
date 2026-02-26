from flask import Flask, render_template, session, request, jsonify, redirect
import os
from extensions import db
from models import Game
from chess_logic import (
    create_board, 
    get_fen,
    board_from_fen,
    make_move,
    make_random_ai_move,
)

app = Flask(__name__)
app.secret_key = "dev-secret-key" # Pour session !!!

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "chess.db")

os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
@app.route('/')
def welcome():
    # On cherche la dernière partie créée en base de données
    last_game = Game.query.order_by(Game.created_at.desc()).first()
    
    if last_game:
        # On restaure la session à partir de la base de données
        session["game_id"] = last_game.id
        session["fen"] = last_game.fen
        return redirect("/board")
    
    return redirect("/new-game")

@app.route('/new-game')
def new_game():
    board = create_board()
    fen = get_fen(board)

    game = Game(fen=fen)
    db.session.add(game)
    db.session.commit()

    session["game_id"] = game.id
    session["fen"] = fen

    return redirect("/board")

@app.route("/play", methods=["POST"])
def play():
    game_id = session.get("game_id")
    if not game_id or "fen" not in session:
        return jsonify({"error": "No active game"}), 400

    data = request.json
    move_uci = data.get("move")
    board = board_from_fen(session["fen"])

    if not make_move(board, move_uci):
        return jsonify({"error": "Illegal move"}), 400

    ai_move = make_random_ai_move(board)
    new_fen = get_fen(board)

    game = Game.query.get(game_id)
    if game:
        game.fen = new_fen
        db.session.commit()

    session["fen"] = new_fen

    return jsonify({
        "player_move": move_uci,
        "ai_move": ai_move,
        "fen": new_fen,
        "ascii": str(board),
        "game_over": board.is_game_over()
    })

@app.route("/board")
def board():
    if "fen" not in session:
        return "Pas de partie commencée."
    board = board_from_fen(session["fen"])
    ascii_board = str(board)

    return render_template("board.html", board = ascii_board)

@app.route("/play-form", methods=["POST"])
def play_form():
    game_id = session.get("game_id")
    if not game_id or "fen" not in session:
        return "No active game"

    move_uci = request.form.get("move")
    board = board_from_fen(session["fen"])

    if not make_move(board, move_uci):
        return "Illegal move"

    make_random_ai_move(board)
    new_fen = get_fen(board)

    # SAUVEGARDE EN BASE
    game = Game.query.get(game_id)
    if game:
        game.fen = new_fen
        db.session.commit()

    session["fen"] = new_fen
    return redirect("/board")

@app.route('/debug-db')
def debug_db():
    games = Game.query.all()
    return jsonify([{"id": g.id, "fen": g.fen} for g in games])