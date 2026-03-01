
var config = {
    position: currentFen,
    draggable: true,
    pieceTheme: '/static/chessboard/img/wikipedia/{piece}.png',
    onDrop: onDrop
};

var board = Chessboard('board', config);

function onDrop(source, target) {
    if (source === target) return "snapback";

    var move = source + target;

    fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ move: move })
    })
    .then(response => response.json())
    .then(data => {

        if (data.error) {
            board.position(currentFen); // rollback
            alert("Coup illégal !");
            return;
        }

        currentFen = data.fen;        // mise à jour FEN locale
        board.position(currentFen);   // affichage nouveau board
    });
}

    function newGame() {
        window.location.href = "/new-game";
    }