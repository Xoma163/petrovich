const SCALE = 1 // step 0.5

const BLOCK_SIZE = 40 * SCALE
const LINE_SIZE = 2 * SCALE
const OUTER_BORDER_SIZE = 4 * SCALE
const PLAYER_SIZE = BLOCK_SIZE / 2

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

let sessionId = undefined


function draw(map, userPos) {
    let width = OUTER_BORDER_SIZE * 2 + BLOCK_SIZE * map[0].length
    let height = OUTER_BORDER_SIZE * 2 + BLOCK_SIZE * map.length
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = "#fff";
    ctx.fillRect(OUTER_BORDER_SIZE, OUTER_BORDER_SIZE, width - 2 * OUTER_BORDER_SIZE, height - 2 * OUTER_BORDER_SIZE);
    drawBlocks(map)
    drawPlayer(userPos)
}

function drawBlocks(map) {
    for (let i = 0; i < map.length; i++) {
        for (let j = 0; j < map[i].length; j++) {
            drawRectangle(i, j, map[i][j])
        }
    }
}

function drawRectangle(i, j, item) {
    const newY = OUTER_BORDER_SIZE + i * BLOCK_SIZE
    const newX = OUTER_BORDER_SIZE + j * BLOCK_SIZE
    if (item.visibility === "REVEALED") {
        ctx.fillStyle = "#fff2cc";
    } else if (item.visibility === "HIDDEN") {
        ctx.fillStyle = "#bbb";
    } else if (item.visibility === "SEEN") {
        ctx.fillStyle = "#fff";
    }
    ctx.fillRect(newX, newY, BLOCK_SIZE, BLOCK_SIZE);

    if (item.visibility === "HIDDEN") {
        return;
    }

    ctx.fillStyle = "#000";
    if (item.wallUp) {
        ctx.fillRect(newX, newY, BLOCK_SIZE, LINE_SIZE);
    }
    if (item.wallDown) {
        ctx.fillRect(newX, newY + BLOCK_SIZE - LINE_SIZE, BLOCK_SIZE, LINE_SIZE);
    }
    if (item.wallLeft) {
        ctx.fillRect(newX, newY, LINE_SIZE, BLOCK_SIZE);
    }
    if (item.wallRight) {
        ctx.fillRect(newX + BLOCK_SIZE - LINE_SIZE, newY, LINE_SIZE, BLOCK_SIZE);
    }
}

function drawPlayer(userPos) {
    const deltaPlus = Math.floor((BLOCK_SIZE - PLAYER_SIZE) / 2)
    const newY = OUTER_BORDER_SIZE + userPos.x * BLOCK_SIZE + deltaPlus
    const newX = OUTER_BORDER_SIZE + userPos.y * BLOCK_SIZE + deltaPlus

    ctx.fillStyle = "#55aa55";
    ctx.fillRect(newX, newY, PLAYER_SIZE, PLAYER_SIZE);
}

window.onload = async () => {
    sessionId = new URLSearchParams(location.search).get("sessionId");
    if (!sessionId) {
        await createGame()
    } else {
        await getSessionGame()
    }
}

window.onkeydown = event => {
    switch (event.code) {
        case 'KeyW':
        case 'ArrowUp':
            doTheMove('up');
            break;
        case 'KeyA':
        case 'ArrowLeft':
            doTheMove('left');
            break;
        case 'KeyS':
        case 'ArrowDown':
            doTheMove('down');
            break;
        case 'KeyD':
        case 'ArrowRight':
            doTheMove('right');
            break;
        default:
    }
}

async function createGame() {
    const response = await fetch(`https://labyrinth.edubovit.net/api/game/create/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: '{"width":30,"height":20,"cellSize":20}'
    });
    const body = await response.json();
    let url = new URL(location.href);
    url.searchParams.set('sessionId', body.id);
    location.href = url.href
}

async function getSessionGame() {
    const response = await fetch(`https://labyrinth.edubovit.net/api/game/${sessionId}/`, {
        method: 'GET',
        headers: {'Content-Type': 'application/json'},
    });
    const body = await response.json();
    draw(body.map.map, {x: body.playerCoordinates.i, y: body.playerCoordinates.j})
}

async function doTheMove(direction) {
    const response = await fetch(`https://labyrinth.edubovit.net/api/game/${sessionId}/${direction}/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
    });
    const body = await response.json();
    draw(body.map.map, {x: body.playerCoordinates.i, y: body.playerCoordinates.j})

    if (body.finish) {
        alert("Молодец какой")
    }
}


// function resize() {
//     $("#canvas").outerHeight($(window).height() - $("#canvas").offset().top - Math.abs($("#canvas").outerHeight(true) - $("#canvas").outerHeight()));
// }
//