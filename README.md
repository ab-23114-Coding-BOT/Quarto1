# Projet 2025 – IA Quarto – Python

## Description

Ce projet consiste à créer une IA qui peut jouer au jeu **Quarto** via un serveur TCP. Le bot communique avec un [serveur principal](https://github.com/qlurkin/PI2CChampionshipRunner/tree/main) pour participer à des parties en réseau et peut jouer automatiquement au jeu (quand un adversaire rejoint lui aussi le serveur) en choisissant intelligemment où placer une pièce et quelle pièce offrir à l’adversaire.

## Le jeu Quarto

Quarto est un jeu de société stratégique contenant 16 pièces différentes, ayant à chaque fois 4 caractéristiques commune : 
- Clair ou foncé
- Rond ou carré
- Creux ou plein
- Petit ou grand
Ces pièces sont placées sur un plateau 4x4 et le but est donc de pouvoir aligner 4 pièces (que ce soit en diagonal, horizontal ou vertical) partageant au moins un attribut commun. La particularité en plus de ce jeu est qu’après avoir joué un tour, la pièce suivante de l’adversaire doit être choisie par le joueur.

## Stratégie de l’IA

- **Placement de la pièce** : Le bot tente de gagner immédiatement en plaçant la pièce reçue si cela crée une ligne, colonne ou diagonale avec 4 pièces ayant un attribut commun. Il utilise la fonction `creates_victory(board, pos, piece)` pour vérifier si la position choisie permet une victoire.
- **Blocage de la victoire de l'adversaire** : Si l’adversaire peut gagner au prochain coup, le bot bloque cette victoire en vérifiant toutes les positions valides et en cherchant si une pièce peut créer une ligne de 4 pièces gagnantes. La fonction `blocks_opponent_win(board, current_piece)` est utilisée pour déterminer la position à bloquer.
- **Minimax** : Le bot utilise un algorithme Minimax avec élagage alpha-bêta pour choisir le meilleur coup sur plusieurs niveaux en utilisant la fonction `minimax(board, current_piece, depth, maximizing_player, alpha, beta)`. Il est utilisé en fin de partie (moins de 6 cases libres) pour des raisons de facilité de temps, de performance et d’efficacité stratégique (il est plus facile de placer une pièce avec des fonctions moins complexes que de calculer le meilleur emplacement quand le plateau est encore vide)
- **Choix de la pièce à donner** : Le bot sélectionne une pièce à donner à l’adversaire tout en évitant de lui donner une pièce qui lui permettrait de gagner. Il utilise la fonction `is_bad_gift(board_after_move, given_piece)` pour s’assurer que la pièce donnée ne permettra pas à l’adversaire de gagner immédiatement.
- **Scores heuristiques** : Lorsqu’il s'agit de choisir une position, le bot utilise une approche basée sur un score heuristique pour déterminer la qualité d'une position donnée. Il utilise la fonction `position_score(board, pos, piece)` pour évaluer la position la plus avantageuse.

## Fonctionnalités principales

- Gestion du plateau et détection des lignes, colonnes, diagonales.  
- Évaluation des positions gagnantes et potentielles.  
- Simulation d’état du plateau pour anticiper les coups futurs.  
- Algorithme Minimax avec élagage alpha-bêta pour connaître la meilleure pièce sur plusieurs coups.  
- Serveur TCP multi-threadé pour gérer les connexions entrantes.  
- Communication JSON avec un serveur principal pour échanger les coups.

## Bibliothèques utilisées

- `socket` : Pour la communication réseau TCP.  
- `threading` : Pour gérer plusieurs connexions clients simultanément.  
- `json` : Pour sérialiser/désérialiser les messages échangés.  
- `random` : Pour sélectionner aléatoirement parmi plusieurs options valides.

## Lancer le bot

1. Modifier la variable `IpServeur` avec l’adresse IP du serveur principal.  
2. Lancer le script Python.  
3. Le bot s’inscrit automatiquement au serveur principal et attend les parties.  
4. Garder la console ouverte pour maintenir le bot actif.

## Auteur

[Chouaa Mohamed - 23105]
[Bekhakh Abdeljalil – 23114]
