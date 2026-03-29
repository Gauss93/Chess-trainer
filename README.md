# Chess Trainer

Application web d’échecs avec IA, API REST et persistance en base de données.

Développée avec Flask, SQLAlchemy et SQLite/PostgreSQL, elle permet de jouer une partie complète, sauvegarder l’état du jeu et interagir via une interface web ou une API.

## Démo
👉 https://chess-trainer-nrks.onrender.com
⚠️ L’application peut mettre quelques secondes à démarrer (hébergement gratuit).

## Aperçu

### Interface principale
![Interface](./screenshots/interface.png)

### API / Backend
![API](./screenshots/API.png)

### Partie en cours
![Gameplay](./screenshots/gameplay.gif)


## Ce que ce projet démontre

- développement d’une application web full stack fonctionnelle ;
- conception d’une architecture backend claire (Flask, séparation des responsabilités) ;
- implémentation d’une API REST pour piloter une logique métier complexe ;
- gestion de la persistance avec SQLAlchemy (SQLite / PostgreSQL) ;
- manipulation d’un état applicatif (FEN) pour reconstruire une partie ;
- intégration d’une bibliothèque métier externe fiable (`python-chess`).

## Fonctionnalités

- création d'une nouvelle partie ;
- choix de la couleur du joueur ;
- jeu contre une IA basique ;
- validation des coups;
- affichage interactif du plateau ;
- gestion de la promotion des pions ;
- reprise de la dernière partie active ;
- gestion d'un contrôle du temps côté serveur ;
- prise en charge de SQLite et PostgreSQL.

## Stack technique

### Backend

- Python
- Flask
- SQLAlchemy
- SQLite / PostgreSQL
- Docker Compose
- python-chess

### Frontend

- HTML
- CSS
- JavaScript
- Chessboard.js

## Architecture

Le projet repose sur une séparation simple des responsabilités :

- `app.py` : configuration Flask, routes, session utilisateur, persistance et gestion du chrono ;
- `chess_logic.py` : logique métier liée au plateau, aux coups et à l'IA simple ;
- `models.py` : modèles SQLAlchemy ;
- `extensions.py` : initialisation des extensions Flask ;
- `templates/` : vues HTML ;
- `static/` : styles, scripts et ressources du plateau.

## Installation rapide

### Prérequis

- Python 3 ;
- `pip` ;
- Docker Desktop uniquement si vous souhaitez utiliser PostgreSQL via Docker Compose.

### Option 1 - Lancement local avec SQLite

Le moyen le plus simple de tester le projet est d'utiliser SQLite, sans Docker.

Si un fichier `.env` contient une variable `DATABASE_URL` pointant vers PostgreSQL, il faut la supprimer ou la commenter avant le lancement. Sans cette variable, l'application utilise automatiquement SQLite dans `instance/chess.db`.

```bash
git clone https://github.com/Gauss93/chess-trainer.git
cd chess-trainer
python -m venv .venv
```

Sous Windows :

```powershell
.\.venv\Scripts\Activate.ps1
```

Sous Linux / macOS :

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Lancer l'application :

```bash
python app.py
```

Accès local :

```text
http://127.0.0.1:5000
```

### Option 2 - Lancement avec PostgreSQL

Démarrer PostgreSQL :

```bash
docker compose up -d
```

Puis définir dans `.env` :

```env
DATABASE_URL=postgresql://user:password@localhost:5432/chess_db
```

Lancer ensuite l'application :

```bash
python app.py
```

## Exemple de test API

Création d'une session PowerShell :

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
```

Initialisation d'une partie :

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/new-game" `
  -WebSession $session
```

Envoi d'un coup :

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/play" `
  -Method Post `
  -WebSession $session `
  -Body '{"move":"e2e4"}' `
  -ContentType "application/json"
```

## Limites actuelles et pistes d'amélioration

Le projet est volontairement simple et peut encore évoluer sur plusieurs points :

- amélioration du niveau de l'IA ;
- ajout d'un historique des coups ;
- authentification utilisateur ;
- système de classement ;
- déploiement en ligne.
