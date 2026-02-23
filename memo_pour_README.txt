
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