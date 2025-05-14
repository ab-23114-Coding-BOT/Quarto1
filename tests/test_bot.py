import random
from Clients.Bot import get_valid_positions, get_remaining_pieces, choose_move

ALL_PIECES = [
    "BDEC","BDEP","BDFC","BDFP",
    "BLEC","BLEP","BLFC","BLFP",
    "SDEC","SDEP","SDFC","SDFP",
    "SLEC","SLEP","SLFC","SLFP"
]

def test_get_valid_positions_all_empty():
    board = [None, None, None, None]
    assert get_valid_positions(board) == [0, 1, 2, 3]

def test_get_valid_positions_some_filled():
    board = ["X", None, "Y", None]
    assert get_valid_positions(board) == [1, 3]

def test_get_valid_positions_no_empty():
    board = ["A", "B", "C", "D"]
    assert get_valid_positions(board) == []

def test_get_remaining_pieces_no_current():
    board = [None, "BDEC", None]
    expected = [p for p in ALL_PIECES if p != "BDEC"]
    result = get_remaining_pieces(board, None)
    assert sorted(result) == sorted(expected)

def test_get_remaining_pieces_with_current_already_used():
    board = ["BDEP", "BDFC"]
    # current_piece déjà dans board = on ne l'ajoute pas deux fois
    expected = [p for p in ALL_PIECES if p not in ["BDEP", "BDFC"]]
    result = get_remaining_pieces(board, "BDEP")
    assert sorted(result) == sorted(expected)

def test_choose_move_gives_piece_when_none():
    random.seed(0)  # pour reproductibilité
    state = {"board": [None, None, None, None], "piece": None}
    move = choose_move(state)
    assert move["pos"] is None
    assert move["piece"] in get_remaining_pieces(state["board"], None)

def test_choose_move_gives_up_when_full():
    state = {"board": ["X", "Y", "Z"], "piece": "BDEC"}
    move = choose_move(state)
    assert move.get("response") == "give_up"

def test_choose_move_random_play():
    random.seed(1)
    board = [None, "A", None]
    state = {"board": board, "piece": "BDEP"}
    move = choose_move(state)
    assert move["pos"] in get_valid_positions(board)
    assert move["piece"] in get_remaining_pieces(board, "BDEP")
