import socket
import threading
import json
import random

HOST = "0.0.0.0"
PORT = 1234
IpServeur = "192.168.129.13"

TEAM_NAME = "P2"
MATRICULES = ["111", "0000"]

ALL_PIECES = [
    "BDEC","BDEP","BDFC","BDFP",
    "BLEC","BLEP","BLFC","BLFP",
    "SDEC","SDEP","SDFC","SDFP",
    "SLEC","SLEP","SLFC","SLFP"
]

def get_valid_positions(board):
    return [i for i, cell in enumerate(board) if cell is None]

def get_remaining_pieces(board, current_piece=None):
    used = [p for p in board if p is not None and p in ALL_PIECES]
    if current_piece and current_piece in ALL_PIECES and current_piece not in used:
        used.append(current_piece)
    return [p for p in ALL_PIECES if p not in used]

def choose_move(state):
    board = state["board"]
    current_piece = state["piece"]
    remaining = get_remaining_pieces(board, current_piece)
    positions = get_valid_positions(board)

    if current_piece is None:
        return {"pos": None, "piece": random.choice(remaining)}

    if not positions:
        return {"response": "give_up"}

    return {
        "pos": random.choice(positions),
        "piece": random.choice(remaining)
    }

def handle_client(conn):
    with conn:
        buf = ""
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            buf += data
            try:
                req = json.loads(buf)
                buf = ""
                if req["request"] == "ping":
                    conn.sendall((json.dumps({"response": "pong"})+"\n").encode())
                elif req["request"] == "play":
                    move = choose_move(req["state"])
                    conn.sendall((json.dumps({"response":"move","move":move})+"\n").encode())
                elif req["request"] == "give_up":
                    conn.sendall((json.dumps({"response":"give_up"})+"\n").encode())
            except json.JSONDecodeError:
                continue

def start_tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

def subscribe_to_main_server():
    data = {"request":"subscribe","port":PORT,"name":TEAM_NAME,"matricules":MATRICULES}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((IpServeur,3000))
        sock.sendall((json.dumps(data)+"\n").encode())
        print(sock.recv(1024).decode())

if __name__ == "__main__":
    threading.Thread(target=start_tcp_server, daemon=True).start()
    subscribe_to_main_server()
    input()
