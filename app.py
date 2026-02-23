from flask import Flask, render_template, session, request, jsonify
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
    return render_template('welcome.html')

@app.route('/new-game')
def new_game():
    board = create_board()
    session["fen"] = get_fen(board)
    return f"Nouvelle partie créée"

@app.route("/play", methods=["POST"])
def play():
    if "fen" not in session:
        return jsonify({"error": "No active game"}), 400

    data = request.get_json(silent=True)
    if not data or "move" not in data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    move_uci = data["move"]

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

