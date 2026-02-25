from flask import Flask, render_template, session, request, jsonify, redirect
from chess_logic import (
    create_board, 
    get_fen,
    board_from_fen,
    make_move,
    make_random_ai_move,
)

app = Flask(__name__)
app.secret_key = "dev-secret-key" # Pour session !!!

@app.route('/')
def welcome():
    if "fen" not in session:
        return redirect("/new-game")
    return redirect("/board")

@app.route('/new-game')
def new_game():
    board = create_board()
    session["fen"] = get_fen(board)
    return redirect("/board")

@app.route("/play", methods=["POST"])
def play():
    if "fen" not in session:
        return jsonify({"error": "No active game"}), 400

    data = request.json
    move_uci = data.get("move")

    board = board_from_fen(session["fen"])

    if not make_move(board, move_uci):
        return jsonify({"error": "Illegal move"}), 400

    ai_move = make_random_ai_move(board)

    session["fen"] = get_fen(board)

    return jsonify({
        "player_move": move_uci,
        "ai_move": ai_move,
        "fen": session["fen"],
        "ascii": str(board),
        "game_over": board.is_game_over()
    })

@app.route("/board")
def board():
    if "fen" not in session:
        return "Pas de partie commencée."
    board = board_from_fen(session["fen"])
    ascii_board = str(board)

    # return f"<pre>{ascii_board}</pre>"

    return render_template("board.html", board = ascii_board)

@app.route("/play-form", methods=["POST"])
def play_form():
    if "fen" not in session:
        return "No active game"

    move_uci = request.form.get("move")

    board = board_from_fen(session["fen"])

    if not make_move(board, move_uci):
        return "Illegal move"

    make_random_ai_move(board)

    session["fen"] = get_fen(board)

    return redirect("/board")
