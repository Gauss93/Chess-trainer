
function onDragStart(source, piece) {
    // Bloquer si ce n'est pas le tour du joueur
    if (
        (playerColor === "white" && piece.startsWith("b")) ||
        (playerColor === "black" && piece.startsWith("w"))
    ) {
        return false;
    }

    // Vérifier que c'est le bon tour
    if (
        (playerColor === "white" && !currentFen.includes(" w ")) ||
        (playerColor === "black" && !currentFen.includes(" b "))
    ) {
        return false;
    }
}

async function onDrop(source, target) {
    if (source === target) return "snapback";

    let move = source + target;

    // Vérifier si c'est une promotion
    let piece = board.position()[source];

    if (
        piece &&
        piece[1] === "P" &&
        (
            (piece[0] === "w" && target[1] === "8") ||
            (piece[0] === "b" && target[1] === "1")
        )
    ) {
        
        let promotion = await showPromotionModal(piece[0]);
        move += promotion;
    
    }

    fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ move: move })
    })
    .then(response => response.json())
    .then(data => {

        if (data.error) {
            board.position(currentFen);
            alert("Coup illégal !");
            return;
        }

        currentFen = data.fen;
        board.position(currentFen);
    });
}

function showPromotionModal(color) {

    return new Promise(resolve => {

        const modal = document.getElementById("promotion-modal");
        const images = modal.querySelectorAll("img");

        images.forEach(img => {
            img.src = `/static/chessboard/img/wikipedia/${color}${img.dataset.piece.toUpperCase()}.png`;

            img.onclick = () => {
                modal.classList.add("hidden");
                resolve(img.dataset.piece);
            };
        });

        modal.classList.remove("hidden");
    });
}

var config = {
    position: currentFen,
    draggable: true,
    orientation: playerColor,
    pieceTheme: '/static/chessboard/img/wikipedia/{piece}.png',
    onDrop: onDrop,
    onDragStart: onDragStart
};

var board = Chessboard('board', config);