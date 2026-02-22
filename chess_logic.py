import chess

def create_board():
    return chess.Board()

def get_board_ascii(board):
    return str(board)

def get_fen(board):
    return board.fen()

def board_from_fen(fen):
    return chess.Board(fen)

def make_move(board, move_uci):
    move = chess.Move.from_uci(move_uci)
    if move in board.legal_moves:
        board.push(move)
        return True
    return False

