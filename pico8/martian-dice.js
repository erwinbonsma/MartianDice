const gpio_GameControl = 0;
const gpio_RoomControl = 1;
const gpio_OutControl = 2;
const gpio_Dump = 3;
const gpio_Move = 4;
const gpio_RoomStatus = 8;
const gpio_Room = 9;
const gpio_Throw = 16;
const gpio_SideDice = 21;
const gpio_EndCause = 26;
const gpio_TurnScore = 27; // Only valid when EndCause != 0
const gpio_TotalScore = 28;
const gpio_CurrentPos = 29; // Only valid when EndCause != 0
const gpio_TurnCounters = 32;

const DIE_IDS = {
	"Ray": 1,
	"Tank": 2,
	"Chicken": 3,
	"Cow": 4,
	"Human": 5
};

const DIE_NAMES = Object.entries(DIE_IDS).reduce((d, [name, index]) => {
	d[index] = name;
	return d;
}, {});

const PHASE_IDS = {
	"Throwing": 1,
	"Thrown": 2,
	"MovedTanks": 3,
	"PickDice": 4,
	"PickedDice": 5,
	"CheckPass": 6,
	"Done": 7
};

var md_myName;

// Room status
var md_roomId;
var md_socket;
var md_joinAttempts = 0;
var md_host;
var md_clients = [];
var md_bots = {};
var md_nextBotId = 0;

// Game status
var md_game;
var md_gameNext;
var md_turnStates = [];
var md_botMoveTriggered;

function playerId(playerName) {
	const players = md_game.players;
	for (var i = 0; i < players.length; i++) {
		if (players[i] === playerName) {
			return i+1;
		}
	}
	return 0;
}

function isHost() {
	return md_myName === md_host;
}

function isAwaitingMove() {
	return md_turnStates.length == 0 && !!md_game;
}

function isBotMove() {
	return isAwaitingMove() && md_bots[md_game.active_player];
}

function isMyMove() {
	return isAwaitingMove() && md_game.active_player === md_myName;
}

function welcomeNewClients(prevClients) {
	const newClients = new Set(md_clients);
	prevClients.forEach(oldClient => { newClients.delete(oldClient); });
	newClients.delete(md_myName);

	if (newClients.size > 0) {
		console.log("Welcoming new clients:", newClients);
		const optGameConfig = md_gameNext ? {
			game_state: md_gameNext
		} : {};

		md_socket.send(JSON.stringify({
			action: "send-welcome",
			room_id: md_roomId,
			to_clients: [...newClients],
			game_config: {
				bots: md_bots,
				next_bot_id: md_nextBotId
			},
			...optGameConfig
		}));
	}
}

function triggerBotMove() {
	if (md_botMoveTriggered || !isHost() || !isBotMove()) {
		return
	}

	const activePlayer = md_game.active_player;
	const behaviour = md_bots[activePlayer];

	md_socket.send(JSON.stringify({
		action: "bot-move",
		game_id: md_roomId,
		game_state: md_game,
		bot_behaviour: behaviour
	}));
	md_botMoveTriggered = true;
}

function handleMessage(event) {
	const msg = JSON.parse(event.data);
	console.log("Message:", msg);
	switch (msg.type) {
		case "clients":
			const prevClients = md_clients;
			md_clients = msg.clients;
			md_host = msg.host;
			if (pico8_gpio[gpio_RoomStatus] == 2) {
				// Signal that room was joined successfully;
				pico8_gpio[gpio_RoomStatus] = 3;
			}
			if (isHost()) {
				welcomeNewClients(prevClients);
			}
			break;
		case "game-config":
			md_bots = msg.game_config.bots;
			md_nextBotId = msg.game_config.next_bot_id;
			break;
		case "game-state":
			if (md_gameNext && md_gameNext.id !== msg.state.prev_id) {
				console.warn(`Unexpected state transition: ${md_gameNext.id} != ${msg.state.prev_id}`);
			}

			md_gameNext = msg.state;
			if (!md_game) {
				md_game = md_gameNext;
			}

			md_turnStates = msg.turn_state_transitions;
			md_turnStates.push(md_gameNext.turn_state);
			md_botMoveTriggered = false;

			break;
		case "response":
			if (msg.status === "error") {
				console.error(msg.details);
			}
			break;
	}
}

function joinRoom() {
	console.assert(pico8_gpio[gpio_RoomStatus] == 2);
	console.assert(md_joinAttempts > 0);

	const handleResponseMessage = (event) => {
		const msg = JSON.parse(event.data);

		if (msg.type === "response" && msg.status === "error") {
			if (md_joinAttempts > 0) {
				console.warn("Failed to join room. Retrying");
				joinRoom();
			} else {
				// TODO: Signal failure to Pico-8
			}
		} else {
			md_roomId = msg.room_id;			
		}

		md_socket.removeEventListener('message', handleResponseMessage);
	};

	md_socket.addEventListener('message', handleResponseMessage);

	md_myName = `PICO-8${String.fromCharCode(65 + md_joinAttempts)}`;
	const roomId = gpioGetRoomId();

	console.info(`Joining Room ${roomId}`);

	md_socket.send(JSON.stringify({
		action: "join-room",
		room_id: roomId,
		client_id: md_myName
	}));
	md_joinAttempts -= 1;
}

function createRoom() {
	const handleResponseMessage = (event) => {
		const msg = JSON.parse(event.data);

		if (msg.type === "response" && msg.status === "ok") {
			pico8_gpio[gpio_RoomStatus] = 2;
			gpioSetRoomId(msg.room_id);

			// Only one attempt. Joining a fresly created room should always succeed (as there
			// will never be a client name clash)
			md_joinAttempts = 1;

			joinRoom();
		}

		md_socket.removeEventListener('message', handleResponseMessage);
	};

	md_socket.addEventListener('message', handleResponseMessage);

	md_socket.send(JSON.stringify({
		action: "create-room",
	}));
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

function gpioGetRoomId() {
	var roomId = "";

	for (var i = 0; i < 4; i++) {
		roomId += String.fromCharCode(pico8_gpio[gpio_Room + i]);
	}

	return roomId;
}

function gpioSetRoomId(roomId) {
	for (var i = 0; i < 4; i++) {
		pico8_gpio[gpio_Room + i] = roomId.charCodeAt(i);
	}
}

function gpioUpdateDice(dice, gpioAddress) {
	Object.entries(DIE_IDS).forEach( ([label, id]) => {
		pico8_gpio[gpioAddress + id - 1] = dice[label] || 0;
	});
}

function gpioUpdateScore(turn) {
	var totalScore = md_game.scores[md_game.active_player]

	pico8_gpio[gpio_EndCause] = turn.end_cause_id || 0;

	if (turn.end_cause_id) {
		totalScore += turn.score;

		const currentPos = Object.values(md_game.scores).filter(
			score => (score > totalScore)
		).length + 1;

		pico8_gpio[gpio_TurnScore] = turn.score;
		pico8_gpio[gpio_CurrentPos] = currentPos;
	}

	pico8_gpio[gpio_TotalScore] = totalScore;
}

function gpioUpdateTurn(turn) {
	console.log("Writing new turn status:", turn);

	if (turn.phase === "Throwing" && turn.throw_count === 0) {
		md_game = md_gameNext;
	}

	gpioUpdateDice(turn.throw || {}, gpio_Throw);
	gpioUpdateDice(turn.side_dice || {}, gpio_SideDice);
	gpioUpdateScore(turn);

	pico8_gpio[gpio_TurnCounters] = md_game.round;
	pico8_gpio[gpio_TurnCounters + 1] = playerId(md_game.active_player);
	pico8_gpio[gpio_TurnCounters + 2] = turn.throw_count;
	pico8_gpio[gpio_TurnCounters + 3] = PHASE_IDS[turn.phase];

	// Signal when move is expected
	pico8_gpio[gpio_OutControl] = isMyMove() ? 0 : 2;
	console.info("isMyMove", isMyMove());

	pico8_gpio[gpio_GameControl] = 1; // Ready to read
}

function gpioHandleRoomCommands() {
	if (pico8_gpio[gpio_RoomStatus] == 1) {
		// Fresh attempt to join room
		console.log("Initiating room join");
		
		pico8_gpio[gpio_RoomStatus] = 2;
		md_joinAttempts = 8;

		connectToServer(joinRoom);
	}
	else if (pico8_gpio[gpio_RoomStatus] == 6) {
		console.log("Initiating room creation");

		pico8_gpio[gpio_RoomStatus] = 7;

		connectToServer(createRoom);
	}
	else if (pico8_gpio[gpio_RoomStatus] == 4) {
		console.log("Initiating room exit");
		leaveRoom();
	}
}

function gpioHandleMove() {
	if (pico8_gpio[gpio_OutControl] != 1) {
		return
	}

	assert(isMyMove());
	const move = pico8_gpio[gpio_Move];
	if (move >= 1 && move <= 5) {
		assert(move != 2);
		md_socket.send(JSON.stringify({
			action: "move",
			game_id: md_roomId,
			pick_die: DIE_NAMES[move],
			game_state: md_game
		}));
	} else {
		md_socket.send(JSON.stringify({
			action: "move",
			game_id: md_roomId,
			pass: move == 6,
			game_state: md_game
		}));
	}

	pico8_gpio[gpio_OutControl] = 2;
}

function dump() {
	console.log("CTRL_IN_GAME  =", pico8_gpio[gpio_GameControl]);
	console.log("CTRL_IN_ROOM  =", pico8_gpio[gpio_RoomControl]);
	console.log("CTRL_OUT      =", pico8_gpio[gpio_OutControl]);
	console.log("ROOM_STATUS   =", pico8_gpio[gpio_RoomStatus]);
	console.log("ROOM          =", gpioGetRoomId());

	console.log("md_game =", md_game);
	console.log("md_gameNext =", md_gameNext);
	console.log("md_turnStates =", md_turnStates);
}

function gpioUpdate() {
	if (pico8_gpio[gpio_Dump] != 0) {
		pico8_gpio[gpio_Dump] = 0;
		dump();
	}

	gpioHandleRoomCommands();
	gpioHandleMove();

	if (pico8_gpio[gpio_GameControl] == 0) {
		if (md_turnStates.length > 0) {
			const turnState = md_turnStates[0];

			md_turnStates = md_turnStates.slice(1);
			gpioUpdateTurn(turnState);

			if (md_turnStates.length === 0) {
				md_game = md_gameNext;
			}
		}
	}
}

function md_update() {
	gpioUpdate();
	triggerBotMove();
}

window.setInterval(md_update, 30);
console.log("Loaded martian-dice.js");