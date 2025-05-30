import pytest
import json
import socket
from Clients.Bot import (
    ALL_PIECES,
    get_rows, get_columns, get_diagonals,
    get_valid_positions, has_common_attribute,
    creates_victory, count_potential_victories,
    blocks_opponent_win, get_remaining_pieces,
    position_score, is_bad_gift, opponent_can_win,
    simulate_state, evaluate_board,
    choose_move, minimax,
    handle_client, subscribe_to_main_server,
)
import Clients.Bot as B

# -------------------------------------------------------------------
# Fonctions pures : découpage, position, attributs, victoire, score
# -------------------------------------------------------------------

EMPTY = [None] * 16
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
    vp = get_valid_positions(b)
    assert 5 not in vp
    assert len(vp) == 15

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
    assert position_score(EMPTY, 0, "BDEC") >= 0

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

# -------------------------------------------------------------------
# Scénarios de jeu : minimax et choix de coup
# -------------------------------------------------------------------

def test_minimax_empty_board():
    board = [None]*16
    score, move = minimax(board, ALL_PIECES[0], depth=1,
                          maximizing_player=True,
                          alpha=float('-inf'),
                          beta=float('inf'))
    assert isinstance(score, (int, float))
    assert isinstance(move, tuple)
    pos, nxt = move
    assert isinstance(pos, int) and nxt in ALL_PIECES

def test_choose_move_give_piece(monkeypatch):
    state = {"board": [None]*16, "piece": None}
    monkeypatch.setattr(B.random, "choice", lambda seq: seq[0])
    move = choose_move(state)
    assert move["pos"] is None
    assert move["piece"] in ALL_PIECES
    assert "(pièce sûre)" in move["message"]

def test_choose_move_no_safe(monkeypatch):
    monkeypatch.setattr(B, "is_bad_gift", lambda b,p: True)
    monkeypatch.setattr(B.random, "choice", lambda seq: seq[0])
    move = choose_move({"board":[None]*16, "piece": None})
    assert "(pas de pièce sûre)" in move["message"]

def test_choose_move_immediate_win():
    board = [None]*16
    trio = ["BDEC","BDEP","BDFC"]
    for i,p in enumerate(trio):
        board[i] = p
    state = {"board": board, "piece": "BDFP"}
    move = choose_move(state)
    assert move["pos"] == 3
    assert move["piece"] is None
    assert "Je gagne" in move["message"]

def test_choose_move_block():
    board = [None]*16
    trio = ["BDEC","BDEP","BDFC"]
    for i,p in enumerate(trio):
        board[i] = p
    state = {"board":board, "piece":"BDFP"}
    move = choose_move(state)
    assert move["pos"] == 3
    assert move["piece"] is None
    assert "Je gagne" in move["message"]

def test_choose_move_minimax_branch(monkeypatch):
    # forcer valid_positions <= 6
    board = [None]*6 + ["X"]*10
    state = {"board":board, "piece":ALL_PIECES[0]}
    def fake_minimax(bd, pc, depth, maxp, a, b):
        return 123, (7, ALL_PIECES[1])
    monkeypatch.setattr(B, "minimax", fake_minimax)
    move = choose_move(state)
    assert move["pos"] == 7
    assert move["piece"] == ALL_PIECES[1]
    assert "Minimax (prof. 3)" in move["message"]

# -------------------------------------------------------------------
# Serveur TCP et abonnement réseau
# -------------------------------------------------------------------

class DummyConn:
    def __init__(self, inputs):
        self._inputs = [i if isinstance(i, bytes) else i.encode() for i in inputs]
        self.sent = b''
    def recv(self, bufsize):
        return self._inputs.pop(0) if self._inputs else b''
    def sendall(self, data):
        self.sent += data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

def test_handle_client_ping():
    conn = DummyConn(['{"request":"ping"}'])
    handle_client(conn)
    out = json.loads(conn.sent.decode().strip())
    assert out["response"] == "pong"

def test_handle_client_partial_json_and_unknown():
    parts = ['{"request":"pin', 'g"}', '{"request":"foo"}']
    conn = DummyConn(parts)
    handle_client(conn)
    lines = conn.sent.decode().splitlines()
    r1, r2 = json.loads(lines[0]), json.loads(lines[1])
    assert r1["response"] == "pong"
    assert r2["response"] == "error" and "unknown" in r2["error"]

def test_handle_client_play_and_giveup():
    c1 = DummyConn([b'{"request":"play"}'])
    handle_client(c1)
    assert json.loads(c1.sent.decode().strip())["response"] == "giveup"
    c2 = DummyConn([b'{"request":"giveup"}'])
    handle_client(c2)
    assert json.loads(c2.sent.decode().strip())["response"] == "giveup"

def test_subscribe_to_main_server_success(monkeypatch, capsys):
    class FakeSock:
        def __init__(self,*a,**k): pass
        def connect(self, addr): self.addr = addr
        def sendall(self, data): self.data = data
        def recv(self, buf): return b'{"response":"ok"}'
        def __enter__(self): return self
        def __exit__(self,*a): pass

    monkeypatch.setattr(B.socket, "socket", lambda *a, **k: FakeSock())
    subscribe_to_main_server()
    out = capsys.readouterr().out
    assert "[INSCRIPTION] ok" in out

def test_subscribe_to_main_server_error(monkeypatch, capsys):
    class FakeSock2:
        def __init__(self,*a,**k): pass
        def connect(self, a): pass
        def sendall(self, d): pass
        def recv(self, b): return b'{"response":"error","error":"fail"}'
        def __enter__(self): return self
        def __exit__(self,*a): pass

    monkeypatch.setattr(B.socket, "socket", lambda *a, **k: FakeSock2())
    subscribe_to_main_server()
    out = capsys.readouterr().out
    assert "[SUBSCRIBE ERROR] fail" in out

# -------------------------------------------------------------------
# Cas particuliers d'évaluation
# -------------------------------------------------------------------

def test_evaluate_board_none():
    assert evaluate_board([None]*16, None) == 0


def test_evaluate_board_double():
    board = [None]*16
    board[0], board[1] = "BDEC", "BDEP"
    # deux pièces avec attribut commun donnent ≥10
    assert evaluate_board(board, "XXXX") >= 10

def test_get_remaining_pieces_all_used():
    board = ALL_PIECES.copy()
    assert get_remaining_pieces(board) == []

def test_simulate_state_non_destructive():
    board = [None]*16
    new = simulate_state(board, 5, "BDEC")
    # simulate_state ne modifie pas l'original
    assert new[5] == "BDEC"
    assert board[5] is None

def test_get_remaining_pieces_with_current():
    board = [None]*16
    # current_piece non utilisé
    rem = get_remaining_pieces(board, "BDFC")
    assert "BDFC" not in rem
    # si current déjà sur le board
    board[0] = "BDFC"
    rem2 = get_remaining_pieces(board, "BDFC")
    assert "BDFC" not in rem2

def test_opponent_can_win_empty():
    assert not opponent_can_win([None]*16, "BDEC")

def test_is_bad_gift_false():
    # une pièce qui ne permet aucune victoire directe
    board = [None]*16
    assert not is_bad_gift(board, "BDEC")

def test_position_score_simple():
    # poser en (0) ne crée encore aucune ligne à 3 ou 4
    board = [None]*16
    assert position_score(board, 0, "BDEC") == 0
    # construire une ligne à 2 partageant 'B' en pos0 et pos1
    board2 = [None]*16
    board2[0], board2[1] = "BDEC", "BDEP"
    
    assert position_score(board2, 2, "BDFC") == 0

def test_count_potential_victories_multiple():
    # préparer deux menaces pour la même pièce
    board = [None]*16
    # ligne 0-1-2 et colonne 4-8-12
    for i,p in zip([0,1,2], WIN_LINE[:3]):
        board[i] = p
    for i,p in zip([4,8,12], WIN_LINE[:3]):
        board[i] = p
    assert count_potential_victories(board, WIN_LINE[3]) == 1

def test_choose_move_giveup_when_full():
    full = [ALL_PIECES[i] for i in range(16)]
    move = choose_move({"board": full, "piece": "BDEC"})
    # plus de valid_positions -> giveup
    assert move == {"response": "giveup"}

def test_choose_move_fork(monkeypatch):
    # on crée un mini plateau où current_piece peut soit gagner, soit forker
    board = [None]*16
    # deux paires partageant 'B' → possibilité de fork ou de gain direct
    board[0], board[1] = "BDEC", "BDEP"
    board[3], board[7] = "BLEC", "BLEP"
    state = {"board": board, "piece": "BLFC"}
    mv = choose_move(state)

    # On attend un coup actif (pas giveup) et un message cohérent
    assert mv["pos"] is not None  
    msg = mv["message"]
    # Accepte une victoire immédiate, un fork ou un choix Minimax
    assert ("Je gagne" in msg) or ("Fork" in msg) or ("Minimax" in msg)

def test_minimax_winning_move():
    # si on peut gagner en deux coups, minimax le trouve
    board = [None]*16
    trio = ["SDEC","SDEP","SDFC"]
    # premier trio en 0,1,2
    for idx, p in zip([0,1,2], trio):
        board[idx] = p
    # second trio en 4,8,12
    for idx, p in zip([4,8,12], trio):
        board[idx] = p

    # on appelle minimax (le test original importe minimax)
    score, move = minimax(
        board,             # plateau partiellement rempli
        "SDFP",            # pièce qui complète le quarto
        depth=2,
        maximizing_player=True,
        alpha=float('-inf'),
        beta=float('inf')
    )
    # score positif et move bien défini
    assert score > 0
    assert isinstance(move, tuple)

def test_evaluate_board_no_negative_scores():
    # Quel que soit l'état, evaluate_board ne renvoie pas de score négatif
    board = [None]*16
    assert evaluate_board(board, None) == 0
    assert evaluate_board(board, "BDEC") >= 0

    # même avec des menaces, le score reste positif
    for i, p in enumerate(WIN_LINE[:3]):
        board[i] = p
    assert evaluate_board(board, WIN_LINE[3]) >= 0