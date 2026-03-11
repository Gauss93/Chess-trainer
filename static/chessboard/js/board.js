let clockState = window.initialClock || {
    white_time_left: 600,
    black_time_left: 600,
    active_color: "white",
    is_finished: false,
    result: null
};
let countdownInterval = null;

function formatClock(totalSeconds) {
    const safeSeconds = Math.max(0, totalSeconds);
    const minutes = Math.floor(safeSeconds / 60);
    const seconds = safeSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function getGameStatusMessage() {
    if (clockState.result === "white_time_win") {
        return "Temps ecoule pour les Noirs.";
    }

    if (clockState.result === "black_time_win") {
        return "Temps ecoule pour les Blancs.";
    }

    if (clockState.result === "board_game_over") {
        return "Partie terminee sur l'echiquier.";
    }

    if (clockState.is_finished) {
        return "Partie terminee.";
    }

    return "";
}

function renderClock() {
    document.getElementById("white-clock").textContent = formatClock(clockState.white_time_left);
    document.getElementById("black-clock").textContent = formatClock(clockState.black_time_left);

    document.querySelectorAll(".clock-card").forEach(card => {
        card.classList.toggle("active", card.dataset.color === clockState.active_color && !clockState.is_finished);
    });

    document.getElementById("game-status").textContent = getGameStatusMessage();
}

function stopClock() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
}

function startClock() {
    stopClock();
    renderClock();

    if (clockState.is_finished || !clockState.active_color) {
        return;
    }

    countdownInterval = setInterval(() => {
        if (clockState.is_finished || !clockState.active_color) {
            stopClock();
            renderClock();
            return;
        }

        if (clockState.active_color === "white") {
            clockState.white_time_left = Math.max(0, clockState.white_time_left - 1);
            if (clockState.white_time_left === 0) {
                clockState.is_finished = true;
                clockState.result = "black_time_win";
                clockState.active_color = null;
            }
        } else {
            clockState.black_time_left = Math.max(0, clockState.black_time_left - 1);
            if (clockState.black_time_left === 0) {
                clockState.is_finished = true;
                clockState.result = "white_time_win";
                clockState.active_color = null;
            }
        }

        renderClock();
    }, 1000);
}

function updateClockFromServer(serverClock) {
    if (!serverClock) {
        return;
    }

    clockState = serverClock;
    startClock();
}

function onDragStart(source, piece) {
    if (clockState.is_finished) {
        return false;
    }

    if (
        (playerColor === "white" && piece.startsWith("b")) ||
        (playerColor === "black" && piece.startsWith("w"))
    ) {
        return false;
    }

    if (
        (playerColor === "white" && !currentFen.includes(" w ")) ||
        (playerColor === "black" && !currentFen.includes(" b "))
    ) {
        return false;
    }
}

async function onDrop(source, target) {
    if (clockState.is_finished) {
        return "snapback";
    }

    if (source === target) {
        return "snapback";
    }

    let move = source + target;
    const piece = board.position()[source];

    if (
        piece &&
        piece[1] === "P" &&
        (
            (piece[0] === "w" && target[1] === "8") ||
            (piece[0] === "b" && target[1] === "1")
        )
    ) {
        const promotion = await showPromotionModal(piece[0]);
        move += promotion;
    }

    return fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ move: move })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                board.position(currentFen);
                updateClockFromServer(data.clock);
                alert(data.error);
                return;
            }

            currentFen = data.fen;
            board.position(currentFen);
            updateClockFromServer(data.clock);
        })
        .catch(() => {
            board.position(currentFen);
            alert("Erreur de communication avec le serveur.");
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

const config = {
    position: currentFen,
    draggable: true,
    orientation: playerColor,
    pieceTheme: "/static/chessboard/img/wikipedia/{piece}.png",
    onDrop: onDrop,
    onDragStart: onDragStart
};

const board = Chessboard("board", config);
startClock();
