import socket        
import threading     
import json          
import random        

HOST = "0.0.0.0"     
PORT = 9976          
IpServeur = "172.17.91.203"

TEAM_NAME = "P"
MATRICULES = ["23105", "23114"]

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

def creates_victory(board, pos, piece): #vérifie si poser une pièce à une certaine position donne une victoire
    simulated = board.copy()
    simulated[pos] = piece
    lines = get_rows(simulated) + get_columns(simulated) + get_diagonals(simulated)
    return any(None not in line and has_common_attribute(line) for line in lines)

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
        return {"response": "give_up", "message": "Plus de cases disponibles"}

    for pos in valid_positions: #gagner si possible
        if creates_victory(board, pos, current_piece):
            return {
                "pos": pos,
                "piece": None,
                "message": f"Je gagne couz !!"
            }

    block_pos = blocks_opponent_win(board, current_piece) #si l'adversaire gagne on le bloque
    if block_pos is not None:
        return {
            "pos": block_pos,
            "piece": None,
            "message": f"T'as cru t'allais gagner ??"
        }
    
    if len(valid_positions) <= 6: #utilise minimax à la fin de la partie
        depth = 3 if len(valid_positions) > 4 else 4
        print(f"[MINIMAX] Activation profondeur {depth}")
        _, best = minimax(board, current_piece, depth=depth, maximizing_player=True, alpha=float('-inf'), beta=float('inf'))
        if best:
            pos, next_piece = best
            return {
                "pos": pos,
                "piece": next_piece,
                "message": f"Minimax (prof. {depth}) : je joue {pos}, je donne {next_piece}"
            }

    best_pos = max(valid_positions, key=lambda pos: position_score(board, pos, current_piece)) #ou choisir une position "plutôt bonne"
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

                if request["request"] == "ping":
                    response = {"response": "pong"}

                elif request["request"] == "play":
                    state = request["state"]
                    print("[DEBUG] Plateau actuel :", state["board"])
                    print("[DEBUG] Pièce à jouer  :", state["piece"])
                    move = choose_move(state)

                    #vérification automatique du move proposé
                    board = state["board"]
                    used_pieces = [p for p in board if p is not None]
                    all_available_positions = get_valid_positions(board)
                    errors = []

                    if move["piece"] is not None:
                        if move["piece"] not in ALL_PIECES:
                            errors.append(f"Pièce '{move['piece']}' non reconnue")
                        if move["piece"] in used_pieces:
                            errors.append(f"Pièce '{move['piece']}' déjà utilisée")

                    if move["pos"] is not None:
                        if move["pos"] not in all_available_positions:
                            errors.append(f"Position {move['pos']} invalide")

                    if errors:
                        print("Erreur move", move)
                        for err in errors:
                            print("Erreur suivante :", err)

                    response = {
                        "response": "move",
                        "move": move,
                        "message": move.get("message", "Coup joué")
                    }

                elif request["request"] == "give_up":
                    response = {
                        "response": "give_up",
                        "message": "J'abandonne..."
                    }

                else:
                    response = {"response": "error", "error": "Je comprends pas bro"}

                conn.sendall((json.dumps(response) + "\n").encode())

            except json.JSONDecodeError:
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
        sock.sendall((json.dumps(data) + '\n').encode())

        #afficher la réponse du serveur
        response = sock.recv(1024).decode()
        print("[INSCRIPTION]", response)

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