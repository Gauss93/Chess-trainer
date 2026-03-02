# ♟️ Chess Trainer

Application web d’échecs développée en **Python / Flask** permettant de jouer contre une IA basique (coup aléatoire), avec persistance des parties en base **SQLite**.

---

## 🎯 Objectif du projet

Ce projet a été conçu pour démontrer :

- Une architecture backend propre
- Une séparation stricte logique métier / contrôleur
- Une gestion d’état via FEN
- Une API REST testable indépendamment du frontend
- Une interface interactive (drag & drop)
- Une persistance avec SQLAlchemy

---

## 🚀 Fonctionnalités

- Création d’une nouvelle partie
- Jeu contre une IA aléatoire
- Plateau interactif (Chessboard.js)
- Validation des coups via python-chess
- Gestion propre de la promotion des pions (UI clickable)
- Sauvegarde automatique des parties en SQLite
- Reprise de la partie active
- Backend entièrement testable via API REST

---

## 🏗️ Architecture

### Principe fondamental


app.py → Gestion HTTP, sessions, routes
chess_logic.py → Règles du jeu (python-chess uniquement)
models.py → Modèle SQLAlchemy
extensions.py → Initialisation des extensions
templates/ → Vues HTML
static/ → CSS + JS


### 🔒 Gestion d’état

- Aucun objet `Board` global
- L’état du jeu est stocké en session via la **FEN (Forsyth-Edwards Notation)**
- Architecture stateless côté serveur
- Compatible multi-utilisateurs
- Reconstruction rapide du plateau

Exemple de FEN initiale :


rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

---

## 🛠️ Stack Technique

### Backend
- Python 3
- Flask
- python-chess
- Flask-SQLAlchemy
- SQLite

### Frontend
- HTML
- CSS custom
- JavaScript
- Chessboard.js

---  

   # 📂 Structure du projet :
    
    chess-trainer/
    │
    ├── app.py
    ├── chess_logic.py
    ├── models.py
    ├── extensions.py
    ├── requirements.txt
    │
    ├── instance/
    │   └── chess.db
    │
    ├── templates/
    │   └── board.html
    │
    └── static/
        ├── style.css
        ├── board.js
        └── chessboard/
    
---

## ⚙️ Installation

### 1️⃣ Cloner le projet

    ```bash
    git clone <repo_url>
    cd chess-trainer

### 2️⃣ Créer un environnement virtuel

    python -m venv .venv

    Windows :

    .\.venv\Scripts\Activate.ps1

    Linux / Mac :

    source .venv/bin/activate
    
### 3️⃣ Installer les dépendances

    pip install -r requirements.txt
    
### 4️⃣ Lancer le serveur

    python app.py

    Accès :

    http://127.0.0.1:5000

# 🧪 Tester le Backend (PowerShell)

### Créer une session
    
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
        
### Initialiser une partie
    
    Invoke-RestMethod `
        -Uri "http://127.0.0.1:5000/new-game" `
        -WebSession $session
          
### Simuler un coup
    
     Invoke-RestMethod `
        -Uri "http://127.0.0.1:5000/play" `
        -Method Post `
        -WebSession $session `
        -Body '{"move":"e2e4"}' `
        -ContentType "application/json"
          
### Réponse attendue
    
    {
        "player_move": "e2e4",
        "ai_move": "c7c5",
        "fen": "...",
        "game_over": false
     }

# 📚 Compétences démontrées

Séparation logique métier / contrôleur

Gestion d’état propre en environnement multi-utilisateur

Utilisation avancée de python-chess

Gestion d’erreurs JSON robuste

Conception d’API REST testable

Persistance avec SQLAlchemy

Intégration frontend interactif

# 🔮 Améliorations futures

Affichage du résultat (victoire / nul / défaite)

Historique des coups

IA plus avancée (ex : Stockfish)

Authentification utilisateur

Dockerisation

PostgreSQL en production

Déploiement cloud (Render / Fly.io / Railway)

