import chess
import random

def create_board():
    return chess.Board()

def get_board_ascii(board):
    return str(board)

def get_fen(board):
    return board.fen()

def board_from_fen(fen):
    return chess.Board(fen)

def make_move(board, move_uci):
    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return False
    
    if move in board.legal_moves:
        board.push(move)
        return True
    return False

def make_random_ai_move(board):
    moves = list(board.legal_moves)

    if not moves:
        return None

    move = random.choice(moves)
    board.push(move)
    return move.uci()
