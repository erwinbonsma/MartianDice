const md_roomId = "PICO";

const gpio_GameControl = 0;
const gpio_RoomControl = 1;
const gpio_OutControl = 2;
const gpio_Dump = 3;
const gpio_RoomStatus = 8;
const gpio_Throw = 16;
const gpio_SideDice = 21;
const gpio_TurnCounters = 32;

const DIE_IDS = {
	"Ray": 1,
	"Tank": 2,
	"Chicken": 3,
	"Cow": 4,
	"Human": 5
};

const PHASE_IDS = {
	"Throwing": 1,
	"Thrown": 2,
	"MovedTanks": 3,
	"PickDice": 4,
	"PickedDice": 5,
	"CheckPass": 6,
	"Done": 7
};

// Room status
var md_socket;
var md_joinAttempts = 0;
var md_host;
var md_clients;
var md_bots = {};
var md_nextBotId = 0;

// Game status
var md_game;
var md_gameNext;
var md_turnStates = [];

function playerId(playerName) {
	const players = md_game.players;
	for (var i = 0; i < players.length; i++) {
		if (players[i] === playerName) {
			return i+1;
		}
	}
	return 0;
}

function handleMessage(event) {
	const msg = JSON.parse(event.data);
	console.log("Message:", msg);
	switch (msg.type) {
		case "clients":
			md_clients = msg.clients;
			md_host = msg.host;
			if (pico8_gpio[gpio_RoomStatus] == 2) {
				// Signal that room was joined successfully;
				pico8_gpio[gpio_RoomStatus] = 3;
			}
			break;
		case "game-config":
			md_bots = msg.game_config.bots;
			md_nextBotId = msg.game_config.next_bot_id;
			break;
		case "game-state":
			md_gameNext = msg.state;
			if (!md_game) {
				md_game = md_gameNext;
			} else if (md_game.id !== md_gameNext.prev_id) {
				console.warn(`Unexpected state transition: ${md_game.id} != ${md_gameNext.prev_id}`);
			}
			md_turnStates = msg.turn_state_transitions;
			md_turnStates.push(md_gameNext.turn_state);
			break;
		case "response":
			if (msg.status === "error") {
				console.error(msg.details);
			} else {
				console.info(msg.details);
			}
			break;
	}
}

function joinRoom() {
	const playerName = `PICO-8${String.fromCharCode(65 + md_joinAttempts)}`;

	md_socket.send(JSON.stringify({
		action: "join-room",
		room_id: md_roomId,
		client_id: playerName
	}));
	md_joinAttempts += 1;

	if (md_joinAttempts < 8) {
		setTimeout(() => {
			if (!md_host) {
				console.warn("Failed to join room. Retrying");
				joinRoom();	
			}
		}, 2000);
	}
}

function leaveRoom() {
	md_socket.send(JSON.stringify({
		action: "leave-room",
		room_id: md_roomId
	}));

	md_socket.close();
	md_socket = null;
	pico8_gpio[gpio_RoomStatus] = 0;

	md_game = null;
	md_turnStates = [];
	md_gameNext = null;
}

function connectToServer(callback) {
	console.log("Connecting to server");

	const socket = new WebSocket("ws://127.0.0.1:8765");
	socket.addEventListener('open', () => {
		console.log("Opened websocket");
		md_socket = socket;
		if (callback) {
			callback();
		}
	});
	socket.addEventListener('error', (event) => {
		console.error("Websocket error:", event.data);
		socket.close();
		md_socket = undefined;
	})
	socket.addEventListener('message', handleMessage);
}

function gpioUpdateDice(dice, gpioAddress) {
	Object.entries(DIE_IDS).forEach( ([label, id]) => {
		pico8_gpio[gpioAddress + id - 1] = dice[label] || 0;
	});
}

function gpioUpdateTurn(turn) {
	console.log("Writing new turn status:", turn);

	if (turn.phase == "Throwing" && turn.throw_count == 1) {
		md_game = md_gameNext;
	}

	gpioUpdateDice(turn.throw || {}, gpio_Throw);
	gpioUpdateDice(turn.side_dice || {}, gpio_SideDice);

	pico8_gpio[gpio_TurnCounters] = md_game.round;
	pico8_gpio[gpio_TurnCounters + 1] = playerId(md_game.active_player);
	pico8_gpio[gpio_TurnCounters + 2] = turn.throw_count;
	pico8_gpio[gpio_TurnCounters + 3] = PHASE_IDS[turn.phase];

	pico8_gpio[gpio_GameControl] = 1; // Ready to read
}

function dump() {
	console.log("CTRL_IN_GAME  =", pico8_gpio[gpio_GameControl]);
	console.log("CTRL_IN_ROOM  =", pico8_gpio[gpio_RoomControl]);
	console.log("CTRL_OUT      =", pico8_gpio[gpio_OutControl]);
	console.log("ROOM_STATUS   =", pico8_gpio[gpio_RoomStatus]);

	console.log("md_game =", md_game);
	console.log("md_gameNext =", md_gameNext);
	console.log("md_turnStates =", md_turnStates);
}

function gpioUpdate() {
	if (pico8_gpio[gpio_Dump] != 0) {
		pico8_gpio[gpio_Dump] = 0;
		dump();
	}

	if (pico8_gpio[gpio_RoomStatus] == 1) {
		// Fresh attempt to join room
		console.log("Initiating room join");
		
		pico8_gpio[gpio_RoomStatus] = 2;
		md_joinAttempts = 0;

		connectToServer(joinRoom);
	}
	if (pico8_gpio[gpio_RoomStatus] == 4) {
		console.log("Initiating room exit");
		leaveRoom();
	}

	if (pico8_gpio[gpio_GameControl] == 0) {
		if (md_turnStates.length > 0) {
			gpioUpdateTurn(md_turnStates[0]);
			md_turnStates = md_turnStates.slice(1);
		}
	}
}

window.setInterval(gpioUpdate, 30);
console.log("Loaded martian-dice.js");