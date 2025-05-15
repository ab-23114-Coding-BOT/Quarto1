import pytest
from Clients.Bot import (
    get_rows, get_columns, get_diagonals,
    get_valid_positions, has_common_attribute,
    creates_victory, count_potential_victories,
    blocks_opponent_win, get_remaining_pieces,
    position_score, is_bad_gift, opponent_can_win,
    simulate_state, evaluate_board
)

# Un plateau vide
EMPTY = [None] * 16

# Un exemple de ligne gagnante (tous partagent le 1er attribut)
WIN_LINE = ["BDEC", "BDEP", "BDFC", "BDFP"]

@pytest.mark.parametrize("board, expected", [
    (list(range(16)), [list(range(4)), list(range(4,8)), list(range(8,12)), list(range(12,16))]),
])
def test_get_rows(board, expected):
    assert get_rows(board) == expected

def test_get_columns():
    board = list(range(16))
    cols = get_columns(board)
    assert cols[0] == [0,4,8,12]
    assert cols[3] == [3,7,11,15]

def test_get_diagonals():
    board = list(range(16))
    diags = get_diagonals(board)
    assert diags[0] == [0,5,10,15]
    assert diags[1] == [3,6,9,12]

def test_get_valid_positions():
    b = EMPTY.copy()
    b[5] = "foo"
    assert 5 not in get_valid_positions(b)
    assert len(get_valid_positions(b)) == 15

def test_has_common_attribute_true():
    assert has_common_attribute(WIN_LINE)

def test_creates_victory_row():
    board = EMPTY.copy()
    for idx, p in zip([0,1,2], WIN_LINE[:3]):
        board[idx] = p
    assert creates_victory(board, 3, WIN_LINE[3])

def test_count_potential_victories():
    board = EMPTY.copy()
    for i,p in enumerate(WIN_LINE[:3]):
        board[i] = p
    assert count_potential_victories(board, WIN_LINE[3]) == 1

def test_blocks_opponent_win():
    board = EMPTY.copy()
    for i,p in enumerate(WIN_LINE[:3]):
        board[i] = p
    assert blocks_opponent_win(board, WIN_LINE[3]) == 3

def test_get_remaining_pieces():
    board = EMPTY.copy()
    board[0] = "BDEC"
    rem = get_remaining_pieces(board)
    assert "BDEC" not in rem
    rem2 = get_remaining_pieces(board, "BLEC")
    assert "BLEC" not in rem2

def test_position_score_basic():
    board = EMPTY.copy()
    assert position_score(board, 0, "BDEC") >= 0

def test_is_bad_gift_and_opponent_can_win():
    board = EMPTY.copy()
    for i,p in enumerate(WIN_LINE[:3]):
        board[i] = p
    assert is_bad_gift(board, WIN_LINE[3])
    assert opponent_can_win(board, WIN_LINE[3])

def test_simulate_state():
    board = EMPTY.copy()
    sim = simulate_state(board, 7, "BDEC")
    assert sim[7] == "BDEC"
    assert board[7] is None

def test_evaluate_board_immediate_win():
    board = EMPTY.copy()
    for i,p in enumerate(WIN_LINE):
        board[i] = p
    assert evaluate_board(board, "BLFP") >= 1000

if __name__ == "__main__":
    pytest.main()
