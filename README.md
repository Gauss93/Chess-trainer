# Chess Trainer

Application web d'echecs developpee en Python avec Flask. Le projet permet de jouer une partie contre une IA simple, de sauvegarder l'etat de jeu en base de donnees et d'afficher un echiquier interactif en interface web.

## Pourquoi ce depot est interessant pour un recruteur

Ce repository montre deux dimensions complementaires :

- une premiere version construite seul, qui reflete mon niveau et mes choix techniques initiaux ;
- une branche `main` sur laquelle je pousse une version amelioree, avec un travail d'optimisation, de structuration et de finition plus avance, en m'appuyant sur Codex comme assistant de developpement.

L'objectif est de rendre visible a la fois :

- ma capacite a concevoir et livrer un projet de maniere autonome ;
- ma capacite a iterer, refactorer et professionnaliser un code existant.

## Lecture des branches

Pour faciliter l'evaluation du projet :

- branche "version initiale" : implementation de reference correspondant a mon travail avant phase d'optimisation ;
- branche `main` : version actuelle du projet, retravaillee pour ameliorer la qualite du code, la robustesse et la presentation globale, avec une phase d'optimisation menee avec l'aide de Codex.

Cette separation permet de voir concretement la progression entre une version fonctionnelle et une version plus aboutie.

## Fonctionnalites

- creation d'une nouvelle partie ;
- jeu contre une IA basique ;
- validation des coups avec `python-chess` ;
- affichage interactif du plateau ;
- gestion de la promotion des pions ;
- sauvegarde des parties avec SQLAlchemy ;
- reprise de la partie active ;
- API REST testable independamment du frontend ;
- gestion d'un controle du temps cote serveur.
- conteneurisation Docker du projet.

## Stack technique

### Backend

- Python
- Flask
- SQLAlchemy
- SQLite
- python-chess

### Frontend

- HTML
- CSS
- JavaScript
- Chessboard.js

## Architecture

Le projet suit une separation simple des responsabilites :

- `app.py` : routes Flask, session utilisateur, persistence et gestion du chrono ;
- `chess_logic.py` : logique metier liee au plateau et aux coups ;
- `models.py` : modeles SQLAlchemy ;
- `extensions.py` : initialisation des extensions Flask ;
- `templates/` : vues HTML ;
- `static/` : fichiers CSS et JavaScript.

L'etat du plateau est stocke via la notation FEN, ce qui permet une gestion de session legere et une reconstruction fiable du jeu.

## Ce que le projet demontre

- conception d'une application web backend/frontend simple mais complete ;
- separation entre logique metier, couche HTTP et persistence ;
- utilisation d'une bibliotheque metier externe (`python-chess`) ;
- mise en place d'une API JSON exploitable et testable ;
- prise en compte de la robustesse applicative avec gestion d'erreurs et persistence ;
- evolution d'un projet personnel vers une version plus maintenable ;
- capacite a utiliser Codex comme levier d'optimisation, de refactorisation et de clarification technique.

## Installation

```bash
git clone <repo_url>
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

Installation des dependances :

```bash
pip install -r requirements.txt
```

Lancement de l'application :

```bash
python app.py
```

Acces local :

```text
http://127.0.0.1:5000
```

## Exemple de test API

Creation d'une session PowerShell :

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

## Evolutions realisees et pistes d'amelioration

Evolutions deja realisees :

- conteneurisation Docker du projet.

Pistes d'amelioration :

- IA plus avancee ;
- historique des coups ;
- authentification utilisateur ;
- base PostgreSQL pour un environnement de production ;
- deploiement cloud.
