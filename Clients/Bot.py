import socket        
import threading     
import json          
import random        

HOST = "0.0.0.0"     
PORT = 2345          
IpServeur = "192.168.129.13"

TEAM_NAME = "BOTKZ"
MATRICULES = ["23114", "23105"]

ALL_PIECES = [
    "BDEC", "BDEP", "BDFC", "BDFP",
    "BLEC", "BLEP", "BLFC", "BLFP",
    "SDEC", "SDEP", "SDFC", "SDFP",
    "SLEC", "SLEP", "SLFC", "SLFP"
]

def get_rows(board): #coupe le board en listes de 4 éléments
    return [board[i:i+4] for i in range(0, 16, 4)]

def get_columns(board):
    return [[board[i + 4 * j] for j in range(4)] for i in range(4)]

def get_diagonals(board):
    return [
        [board[i] for i in [0, 5, 10, 15]],
        [board[i] for i in [3, 6, 9, 12]]
    ]

def get_valid_positions(board): #sert à récupérer les positions vides sur le plateau
    return [i for i, cell in enumerate(board) if cell is None]

def has_common_attribute(pieces): #retourne true si les 4 pièces ont un attribut en commun
    if len(pieces) != 4 or any(p is None for p in pieces):
        return False

    for i in range(4):
        if all(p[i] == pieces[0][i] for p in pieces):
            return True
    return False

def creates_victory(board, pos, piece):
    simulated = board.copy()
    simulated[pos] = piece

    row_start = (pos // 4) * 4
    row = simulated[row_start : row_start + 4]
    if None not in row and has_common_attribute(row):
        return True

    col_idx = pos % 4
    col = [simulated[col_idx + 4*i] for i in range(4)]
    if None not in col and has_common_attribute(col):
        return True

    diag1 = [0, 5, 10, 15]
    if pos in diag1:
        line = [simulated[i] for i in diag1]
        if None not in line and has_common_attribute(line):
            return True

    diag2 = [3, 6, 9, 12]
    if pos in diag2:
        line = [simulated[i] for i in diag2]
        if None not in line and has_common_attribute(line):
            return True

    return False

def count_potential_victories(board, piece): #nbr de lignes où la pièce peut faire un Quarto immédiat
    count = 0
    for pos in get_valid_positions(board):
        if creates_victory(board, pos, piece):
            count += 1
    return count

def blocks_opponent_win(board, current_piece): #fct pour bloquer la victoire de l'adversaire
    valid_positions = get_valid_positions(board)
    for pos in valid_positions:
        if creates_victory(board, pos, current_piece):
            return pos
    return None

def get_remaining_pieces(board, current_piece=None): #retourne la liste des pièces encore disponibles (pièce en cours non inclus)
    used_pieces = [p for p in board if p is not None and p in ALL_PIECES]
    if current_piece and current_piece in ALL_PIECES and current_piece not in used_pieces:
        used_pieces.append(current_piece)
    return [p for p in ALL_PIECES if p not in used_pieces]

def position_score(board, pos, piece): #fct qui permet de voir la meilleur position à jouer
    simulated = board.copy()
    simulated[pos] = piece
    score = 0
    for line in get_rows(simulated) + get_columns(simulated) + get_diagonals(simulated):
        if line.count(None) <= 1 and has_common_attribute([p for p in line if p]):
            score += 1
    return score

def is_bad_gift(board_after_move, given_piece): #prévient si mauvaise pièce pour l'adversaire
    for pos in get_valid_positions(board_after_move):
        if creates_victory(board_after_move, pos, given_piece):
            return True
    return False

def opponent_can_win(board, given_piece): #vérifie si l'adversaire peut directement gagner
    for pos in get_valid_positions(board):
        if creates_victory(board, pos, given_piece):
            return True
    return False

def choose_move(state): #choisir un coup valide en fonction des choix
    board = state["board"]
    current_piece = state["piece"]
    used_pieces = [p for p in board if p is not None]
    remaining_pieces = [p for p in ALL_PIECES if p not in used_pieces]
    valid_positions = get_valid_positions(board)

    if current_piece is None: #cas 1 : donner une pièce à l'adversaire (éviter de l'avantager)
        safe_pieces = [p for p in remaining_pieces if not is_bad_gift(board, p)]
        if safe_pieces:
            piece = random.choice(safe_pieces)
            message = f"Je donne {piece} (pièce sûre)"
        else:
            piece = random.choice(remaining_pieces)
            message = f"Je donne {piece} (pas de pièce sûre)"

        return {
            "pos": None,
            "piece": piece,
            "message": message
        }

    if not valid_positions: #cas 2 : jouer une pièce reçue
        return {"response": "giveup"}

    for pos in valid_positions: #gagner si possible
        if creates_victory(board, pos, current_piece):
            return {
                "pos": pos,
                "piece": None,
                "message": f"Je gagne couz !!"
            }

    block_pos = blocks_opponent_win(board, current_piece)
    if block_pos is not None:
        return {
            "pos": block_pos, "piece": None,
            "message": "T'as cru t'allais gagner ??"
        }

    # détection de fork : jouer toute position créant plus de 2 victoires potentielles
    fork_moves = []
    for pos in valid_positions:
        sim_board = simulate_state(board, pos, current_piece)
        if count_potential_victories(sim_board, current_piece) > 1:
            fork_moves.append(pos)
    if fork_moves:
        pos0 = fork_moves[0]
        sim = simulate_state(board, pos0, current_piece)
        rem = get_remaining_pieces(sim, current_piece)
        safe = [p for p in rem if not opponent_can_win(sim, p)]
        gift = safe[0] if safe else (rem[0] if rem else None)
        return {"pos": pos0, "piece": gift, "message": "Fork !"}
    
        # Si peu de cases restantes, on active Minimax
    if len(valid_positions) <= 6:
        depth = 3
        score, best = minimax(board, current_piece,
                              depth, True,
                              float('-inf'),
                              float('inf'))
        if best:
            pos, next_piece = best
            return {
                "pos": pos,
                "piece": next_piece,
                "message": f"Minimax (prof. {depth})"
            }

    best_pos = max(
        valid_positions,
        key=lambda pos: (
            count_potential_victories(simulate_state(board, pos, current_piece), current_piece),
            position_score(board, pos, current_piece)
        )
    )

    simulated = simulate_state(board, best_pos, current_piece)
    updated_remaining = get_remaining_pieces(simulated, current_piece)
    safe_next_pieces = [p for p in updated_remaining if not opponent_can_win(simulated, p)]

    next_piece = random.choice(safe_next_pieces) if safe_next_pieces else (
        random.choice(updated_remaining) if updated_remaining else None
    )

    return {
        "pos": best_pos,
        "piece": next_piece,
        "message": f"Je joue sur {best_pos} et donne {next_piece or 'aucune'}"
    }

def evaluate_board(board, current_piece): #donne un score en fct des meilleures situations
    if not current_piece:
        return 0

    score = 0
    lines = get_rows(board) + get_columns(board) + get_diagonals(board)

    for line in lines:
        pieces = [p for p in line if p]
        if len(pieces) == 4 and has_common_attribute(pieces):
            score += 1000  #quarto immédiat
        elif len(pieces) == 3 and line.count(None) == 1:
            #vérifie si on peut gagner sur cette ligne
            simulated = line.copy()
            index = simulated.index(None)
            simulated[index] = current_piece
            if has_common_attribute(simulated):
                score += 100  #possibilité de quarto
        elif len(pieces) == 2:
            for i in range(4):
                if all(p[i] == pieces[0][i] for p in pieces):
                    score += 10  #si 2 pièces possèdent un attribut commun
        elif len(pieces) == 1:
            score += 1  # +1 pour une pièce

    if opponent_can_win(board, current_piece):
        score -= 200  #grosse pénalité si la pièce permet à l’adversaire de gagner

    return score

def minimax(board, current_piece, depth, maximizing_player, alpha, beta): #algorithme de jeu minimax pour avoir le meilleur coup
    valid_positions = get_valid_positions(board)

    if depth == 0 or not valid_positions:
        return evaluate_board(board, current_piece), None

    best_move = None

    if maximizing_player:
        max_eval = float('-inf')
        for pos in valid_positions:
            simulated = simulate_state(board, pos, current_piece)
            next_pieces = get_remaining_pieces(simulated, current_piece)
            for next_piece in next_pieces:
                eval, _ = minimax(simulated, next_piece, depth - 1, False, alpha, beta)
                if eval > max_eval:
                    max_eval = eval
                    best_move = (pos, next_piece)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for pos in valid_positions:
            simulated = simulate_state(board, pos, current_piece)
            next_pieces = get_remaining_pieces(simulated, current_piece)
            for next_piece in next_pieces:
                eval, _ = minimax(simulated, next_piece, depth - 1, True, alpha, beta)
                if eval < min_eval:
                    min_eval = eval
                    best_move = (pos, next_piece)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
        return min_eval, best_move

def simulate_state(board, pos, piece):
    simulated = board.copy()
    simulated[pos] = piece
    return simulated

#gérer le client (connexions, etc.)
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

                if request.get("request") == "ping":
                    response = {"response": "pong"}

                elif request.get("request") == "play":
                    try:
                        move = choose_move(request["state"])
                        response = {"response": "move", "move": move}
                    except Exception:
                        # En cas d’erreur, on abandonne
                        response = {"response": "giveup"}

                elif request.get("request") == "giveup":
                    response = {"response": "giveup"}

                else:
                    response = {"response": "error", "error": "unknown request"}

                # Envoi unique de la réponse
                conn.sendall((json.dumps(response) + "\n").encode())

            except json.JSONDecodeError:
                # JSON incomplet, on attend la suite
                continue

#serveur tcp pour écouter les requetes du serveur
def start_tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Ecoute sur {HOST}:{PORT}...")

    while True:
        conn, addr = server.accept()
        #lance un thread pour gérer le client sans bloquer les autres
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

#inscription au serveur
def subscribe_to_main_server():
    data = {
        "request": "subscribe",   
        "port": PORT,                 
        "name": TEAM_NAME,            
        "matricules": MATRICULES      
    }

    #connexion TCP vers le serveur d’inscription
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((IpServeur, 3000))
        sock.sendall((json.dumps(data) + "\n").encode())
        raw = sock.recv(1024).decode()
        reply = json.loads(raw)
        if reply.get("response") != "ok":
            print(f"[SUBSCRIBE ERROR] {reply.get('error')}")
            return
        print("[INSCRIPTION] ok")

if __name__ == "__main__":
    print("[CLIENT] Démarrage client...")

    #démarre le serveur TCP dans un thread parallèle
    threading.Thread(target=start_tcp_server, daemon=True).start()
    print("[CLIENT] TCP server lancé")

    #s’inscrit auprès du serveur central
    subscribe_to_main_server()
    print("[CLIENT] Inscription envoyée. En attente de matchs...")

    #empêche le script de se fermer tout de suite
    input("[PRÊT] Appuie sur Entrée pour garder le client actif...\n")