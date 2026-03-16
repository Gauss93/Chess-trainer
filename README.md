# Chess Trainer

Application web d'echecs developpée en Python avec Flask. Le projet permet de jouer une partie contre une IA simple, de sauvegarder l'état de jeu en base de données et d'afficher un échiquier interactif en interface web.

## Pourquoi ce dépôt est intéressant pour un recruteur

Ce repository montre deux dimensions complémentaires :

- une branche `main`, qui correspond à la base du projet sur laquelle je travaille directement ;
- une branche `ai-refactor`, qui me permet d'aller plus loin avec Codex sur l'optimisation, la structuration et la finition du projet.

L'objectif est de rendre visible à la fois :

- ma capacité à concevoir et livrer un projet de manière autonome ;
- ma capacité à iterer, refactorer et professionnaliser un code existant avec une démarche d'amélioration continue.

## Fonctionnalites

- création d'une nouvelle partie ;
- jeu contre une IA basique ;
- validation des coups avec `python-chess` ;
- affichage interactif du plateau ;
- gestion de la promotion des pions ;
- sauvegarde des parties avec SQLAlchemy ;
- reprise de la partie active ;
- API REST testable indépendamment du frontend ;
- gestion d'un contrôle du temps côté serveur ;
- service PostgreSQL lancable via Docker Compose.

## Stack technique

### Backend

- Python
- Flask
- SQLAlchemy
- SQLite/PostgreSQL
- Docker
- python-chess

### Frontend

- HTML
- CSS
- JavaScript
- Chessboard.js

## Architecture

Le projet suit une séparation simple des responsabilités :

- `app.py` : routes Flask, session utilisateur, persistence et gestion du chrono ;
- `chess_logic.py` : logique métier liée au plateau et aux coups ;
- `models.py` : modèles SQLAlchemy ;
- `extensions.py` : initialisation des extensions Flask ;
- `templates/` : vues HTML ;
- `static/` : fichiers CSS et JavaScript.

L'etat du plateau est stocké via la notation FEN, ce qui permet une gestion de session légère et une reconstruction fiable du jeu.

## Ce que le projet démontre

- conception d'une application web backend/frontend simple mais complète ;
- séparation entre logique métier, couche HTTP et persistence ;
- utilisation d'une bibliotheque métier externe (`python-chess`) ;
- mise en place d'une API JSON exploitable et testable ;
- prise en compte de la robustesse applicative avec gestion d'erreurs et persistence ;
- evolution d'un projet personnel vers une version plus maintenable ;
- capacité à utiliser Codex comme levier d'optimisation, de refactorisation et de clarification technique.

## Installation

### Prerequis

- Python 3 ;
- `pip` ;
- Docker Desktop uniquement si vous souhaitez lancer PostgreSQL via Docker Compose.

### Option 1 - Lancement local simple avec SQLite

Le chemin le plus simple pour tester le projet est d'utiliser SQLite, sans Docker.

Un fichier `.env` est présent avec une variable `DATABASE_URL` pointant vers PostgreSQL, il faut la commenter ou supprimer cette variable avant de lancer l'application. Sans `DATABASE_URL`, l'application bascule automatiquement sur SQLite dans `instance/chess.db`.

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

Installation des dépendances :

```bash
pip install -r requirements.txt
```

Vérifier que `DATABASE_URL` n'est pas définie pour PostgreSQL, puis lancer l'application :

```bash
python app.py
```

Accès local :

```text
http://127.0.0.1:5000
```

### Option 2 - Lancement avec PostgreSQL via Docker Compose

Démarrer PostgreSQL :

```bash
docker compose up -d
```

Puis définir la variable d'environnement suivante dans un fichier `.env` à la racine du projet :

```env
DATABASE_URL=postgresql://user:password@localhost:5432/chess_db
```

Lancement de l'application :

```bash
python app.py
```

Accès local :

```text
http://127.0.0.1:5000
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

## Evolutions réalisees et pistes d'amélioration

Evolutions déjà réalisées :

- mise à disposition d'un service PostgreSQL via Docker Compose.

Pistes d'amélioration :

- IA plus avancee ;
- historique des coups ;
- authentification utilisateur ;
- système de classement (elo) ;
- déploiement cloud.
