python -m venv .venv
--> pour créer un environement venv
.\venv\Scripts\Activate.ps1
--> pour l'activer

------------------------------------------------------------------------------

Flask pour créer le serveur dans un environement venv
Création de route :
@app.route('/')

code uci (ex = e2e4, pour un coup de pion en e4)

app.py sert a recevoir une requete, verifier les cookies et renvoyer une réponse ET RIEN D'AUTRE.
chess_logic sert a tout ce qui concerne les règles des échecs (python-chess) ET RIEN D'AUTRE.

Attention a ne pas utiliser d'objet global !!! Sinon cela fera changer l'échiquier pour tout les utilisateur en même temps.

Tester un coup:

board = create_board()
make_move(board, "e2e4")
print(board) 
--> retourne le plateau en ascii avec le coup joué.

Utiliser la FEN pour session est ce que j'ai trouver de mieux à faire pour manipuler des données rapidement à bas coup de mémoire.

------------------------------------------------------------------------------

Les ligne de commande pour tester le backend:

Etape 1 stocker les cookies, headers et infos de session :
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

Etape 2 Initialiser la nouvelle partie:
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/new-game" `
  -WebSession $session

--> Doit retourner Nouvelle partie créée.

Etape 3 Simuler un coup:
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/play" `
  -Method Post `
  -WebSession $session `
  -Body '{"move":"e2e4"}' `
  -ContentType "application/json"

--> Doit retourner un json avec mon coup joué, celui de l'ia, la FEN, le plateau en ascii et l'état de game-over.

-------------------------------------------------------------------------------

Premier html dans la route /board avec bouton envoyer coup.

une ia qui joue un coup aléatoire est actif aucun challenge pour l'instant.

pip freeze > requirements.txt pour pouvoir envoyer les dépendances déjà installées.

--------------------------------------------------------------------------------

installation de sqlalchemy

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/chess.db"
--> adresse de base
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
--> Une option technique. Elle désactive un système de notification de modifications qui consomme de la mémoire inutilement.
    La documentation officielle recommande de la mettre à False.

db = SQLAlchemy(app)
--> lien avec sqlachemy et l'appli flask

-------------------------------------------------------------------------------

création de la classe Game
grosse aide des llm pour m'aider a configurer la classe 

------------------------------------------------------------------------------

creation de chess.db

Etape 1 import os dans app

Etape 2 créer le dossier instance

Etape 3 j'ai du modifier ma base sqlalchemy 
# Définir le chemin de la base de données de manière robuste
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "chess.db")

# S'assurer que le dossier 'instance' existe
os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

Etape 4 script pour la création 
j'ai créer un fichier create.db pour lancer le script
python create_db.py

------------------------------------------------------------------------------

premier test de sauvegarde

creation de extensions.db pour creation db a exporter
modification des routes play et play-form

enfin modification de la route ('/') la fonction def recherche maintenant une partie commencée.
aide des llm pour configurer cette route.

La sauvegarde fonctionne !!!!
