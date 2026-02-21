import chess

def create_board():
    return chess.Board()

def get_board_ascii(board):
    return str(board)

def make_move(board, move_uci):
    move = chess.Move.from_uci(move_uci)
    if move in board.legal_moves:
        board.push(move)
        return True
    return False

board = create_board()
# --- Coup 1 ---
make_move(board, "d2d4") # Blancs : Pion Dame
make_move(board, "d7d5") # Noirs : Réponse symétrique

# --- Coup 2 ---
make_move(board, "g1f3") # Blancs : Cavalier f3
make_move(board, "g8f6") # Noirs : Cavalier f6

# --- Coup 3 ---
make_move(board, "c1f4") # Blancs : Fou de Londres
make_move(board, "c8f5") # Noirs : Fou de Londres (miroir)

# --- Coup 4 ---
make_move(board, "e2e3") # Blancs : Fermeture de la chaîne
make_move(board, "e7e6") # Noirs : Fermeture de la chaîne

# --- Coup 5 ---
make_move(board, "c2c3") # Blancs : Pyramide de pions
make_move(board, "c7c6") # Noirs : Pyramide de pions

# --- Coup 6 ---
make_move(board, "f1d3") # Blancs : Développement du Fou Roi
make_move(board, "f8d6") # Noirs : Développement du Fou Dame

# --- Coup 7 ---
make_move(board, "b1d2") # Blancs : Cavalier Dame
make_move(board, "b8d7") # Noirs : Cavalier Dame

# --- Coup 8 (Le Roque) ---
make_move(board, "e1g1") # Blancs : Petit roque
print(board)