import socket
import threading
import json

HOST = "0.0.0.0"
PORT = 9976
IpServeur = "192.168.129.13"
TEAM_NAME = "P"
MATRICULES = ["23105", "23114"]

def handle_client(conn):
    with conn:
        buffer = ""
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            buffer += data
            try:
                request = json.loads(buffer)
                buffer = ""
                if request["request"] == "ping":
                    response = {"response": "pong"}
                    conn.sendall((json.dumps(response) + "\n").encode())
            except json.JSONDecodeError:
                continue

def start_tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

def subscribe_to_main_server():
    data = {"request": "subscribe", "port": PORT, "name": TEAM_NAME, "matricules": MATRICULES}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((IpServeur, 3000))
        sock.sendall((json.dumps(data) + "\n").encode())
        response = sock.recv(1024).decode()
        print(response)

if __name__ == "__main__":
    threading.Thread(target=start_tcp_server, daemon=True).start()
    subscribe_to_main_server()
    input()
