from flask import Flask, render_template, session
from chess_logic import create_board, get_fen

app = Flask(__name__)
app.secret_key = "dev-secret-key" # Pour session !!!

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/new-game')
def new_game():
    board = create_board()
    session["fen"] = get_fen(board)
    return f"Nouvelle partie créée.<br>FEN : {session["fen"]}"


