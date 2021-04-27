const serviceEndpoint = "ws://127.0.0.1:8765";

const gpio_GameControl = 0;
const gpio_RoomControl = 1;
const gpio_OutControl = 2;
const gpio_Error = 3;
const gpio_Move = 4;
const gpio_RoomStatus = 5;
const gpio_Room = 6;
const gpio_MyName = 10;
const gpio_Throw = 16;
const gpio_SideDice = 21;
const gpio_EndCause = 26;
const gpio_TurnScore = 27; // Only valid when EndCause != 0
const gpio_TurnCounters = 32;
const gpio_ActivePlayerType = 36;
const gpio_ActivePlayerName = 37;
const gpio_NumClients = 48;
const gpio_NumBots = 49;
const gpio_IsHost = 50;
const gpio_PlayerType = 51;
const gpio_PlayerName = 52;
const gpio_ChatOut_Msg = 64;
const gpio_ChatIn_Msg = 65;
const gpio_ChatIn_SenderId = 66;
const gpio_NumPlayers = 80;
const gpio_Scores = 81; // Listed in turn order
const gpio_TurnOrder = 87; // Client Ids in turn order, 0 when player is not present
const gpio_IsPlayer = 93;
const gpio_Handshake = gpio_GameControl;

const maxPlayerNameLength = 6;

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

const BEHAVIOUR_IDS = {
	"unknown": 0,
	"random": 1,
	"aggressive": 2,
	"defensive": 3,
	"smart": 4
};

const PHASE_IDS = {
	"Throwing": 1,
	"Thrown": 2,
	"MovedTanks": 3,
	"PickDice": 4,
	"PickedDice": 5,
	"CheckPass": 6,
	"Done": 7,
};
const gameEndId = 8;

var md_myName;

// Room status
var md_roomId;
var md_socket;
var md_host;
var md_clients = {}; // key=name, value=id [1..6]
var md_bots = {}; // key=name, value=behaviour (string)
var md_nextBotId = 0;

var md_gpioRoomBatch = null;
var md_gpioRoomUpdates = [];
var md_gpioChats = [];

// Game status
var md_game;
var md_gameNext;
var md_turnStates = [];
var md_botMoveTriggered;
var md_gameEnded;

function sizeOfDict(d) {
	let n = 0;
	Object.keys(d).forEach(() => { n += 1; });
	return n;
}

function playerTurnOrder(playerName) {
	const players = md_game.players;
	for (var i = 0; i < players.length; i++) {
		if (players[i] === playerName) {
			return i+1;
		}
	}
	return 0;
}

function playerNameToId(playerName) {
	const clientId = md_clients[playerName];
	if (clientId) {
		return clientId;
	}
	const botBehaviour = md_bots[playerName];
	if (botBehaviour) {
		return 6 + BEHAVIOUR_IDS[botBehaviour]; 
	}

	// Unknown or disconnected player
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

// Updates md_clients so that it contains all clients in clients list. It ensures that:
// - New clients get a unique id, in range [1..6]
// - Existing clients keep their id
// - The local client is always assigned id 1
//
// It also returns a set with new clients, which may need to be welcomed.
function updateClients(clients) {
	const availableIds = new Set(Array.from({length: 5}, (v, i) => i+2));

	const clientsOld = md_clients;
	md_clients = {}

	// Transfer existing clients
	clients.forEach(name => {
		const id = clientsOld[name];
		if (id) {
			md_clients[name] = id;
			availableIds.delete(id);
		}
	});

	// Ensure current player always has ID 1
	md_clients[md_myName] = 1;

	const addedClients = [];
	// Add clients that appeared
	clients.forEach(name => {
		if (!md_clients[name]) {
			let id;
			for (id of availableIds) { break; }
			md_clients[name] = id;
			availableIds.delete(id);
			addedClients.push(name);	
		}
	});

	return addedClients;
}

function welcomeNewClients(newClients) {
	console.log("Welcoming new clients:", newClients);
	const optGameConfig = (
		// Only share game state when there is an in-progress game
		md_gameNext?.turn_state
		? { game_state: md_gameNext }
		: {}
	);

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
			const addedClients = updateClients(msg.clients);
			md_host = msg.host;
			if (isHost()) {
				if (addedClients.length > 0) {
					if (!md_game || md_gameEnded) {
						// No game in progress, so clear any bots
						md_bots = {};
					}
					welcomeNewClients(addedClients);
				} else if (sizeOfDict(md_clients) == 1 && sizeOfDict(md_bots) == 0) {
					// When alone, automatically add a bot as opponent
					md_nextBotId += 1;
					md_bots[`Bot-${md_nextBotId}`] = "smart";
				}

			}
			gpioPrepareRoomUpdateBatch();
			break;
		case "game-config":
			md_bots = msg.game_config.bots;
			md_nextBotId = msg.game_config.next_bot_id;
			gpioPrepareRoomUpdateBatch();
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
			md_gameEnded = false;

			break;
		case "chat":
			if (msg.message_id) {
				md_gpioChats.push({
					messageId: msg.message_id,
					sender: msg.client_id
				});
			}
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

	const handleResponseMessage = (event) => {
		md_socket.removeEventListener('message', handleResponseMessage);

		const msg = JSON.parse(event.data);

		if (msg.type === "clients") {
			md_roomId = msg.room_id;
			// Signal that room was joined successfully;
			pico8_gpio[gpio_RoomStatus] = 3;
			console.info("Room joined!");

			return;
		}
		if (msg.type === "response" && msg.status === "error") {
			pico8_gpio[gpio_Error] = msg.error_code;
			pico8_gpio[gpio_RoomStatus] = 8;

			return;
		}

		console.warn("Unexpected response message", msg);
	};

	md_socket.addEventListener('message', handleResponseMessage);

	const roomId = gpioGetStr(gpio_Room, 4);
	md_myName = gpioGetStr(gpio_MyName, 6);

	md_bots = {}
	md_nextBotId = 0;

	console.info(`Joining Room ${roomId}`);

	md_socket.send(JSON.stringify({
		action: "join-room",
		room_id: roomId,
		client_id: md_myName
	}));
}

function createRoom() {
	const handleResponseMessage = (event) => {
		md_socket.removeEventListener('message', handleResponseMessage);

		const msg = JSON.parse(event.data);

		if (msg.type === "response") {
			if (msg.status === "ok") {
				gpioSetStr(gpio_Room, 4, msg.room_id);
				pico8_gpio[gpio_RoomStatus] = 2;

				joinRoom();

				return;
			}

			if (msg.status === "error") {
				pico8_gpio[gpio_Error] = msg.error_code;
				pico8_gpio[gpio_RoomStatus] = 8;

				return;
			}
		}

		console.warn("Unexpected response message", msg);
	};

	md_socket.addEventListener('message', handleResponseMessage);

	md_myName = gpioGetStr(gpio_MyName, 6);

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

	const socket = new WebSocket(serviceEndpoint);
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

function gpioPrepareRoomUpdateBatch() {
	md_gpioRoomBatch = {
		numClients: sizeOfDict(md_clients),
		numBots: sizeOfDict(md_bots)
	};

	md_gpioRoomUpdates = [];
	Object.entries(md_clients).forEach(([name, id]) => {
		md_gpioRoomUpdates.push([id, name]);
	});
	Object.entries(md_bots).forEach(([name, behaviour]) => {
		md_gpioRoomUpdates.push([BEHAVIOUR_IDS[behaviour] + 6, name]);
	});

	console.info("Prepared room update:", md_gpioRoomBatch, md_gpioRoomUpdates);
}

function gpioRoomBatchUpdate(batchItem) {
	const [typ, name] = batchItem;

	pico8_gpio[gpio_PlayerType] = typ;
	for (let i = 0; i < maxPlayerNameLength; i++) {
		pico8_gpio[gpio_PlayerName + i] = (i < name.length) ? name.charCodeAt(i) : 0;
	}
}

function gpioGetStr(address, maxLen) {
	var s = "";

	for (var i = 0; i < maxLen; i++) {
		const val = pico8_gpio[address + i];
		if (val == 0) {
			break;
		}
		s += String.fromCharCode(val);
	}

	return s;
}

function gpioSetStr(address, maxLen, s) {
	for (var i = 0; i < maxLen; i++) {
		pico8_gpio[address + i] = (i < s.length) ? s.charCodeAt(i) : 0;
	}
}

function gpioUpdateDice(dice, gpioAddress) {
	Object.entries(DIE_IDS).forEach( ([label, id]) => {
		pico8_gpio[gpioAddress + id - 1] = dice[label] || 0;
	});
}

function gpioUpdateTurnScore(turn) {
	pico8_gpio[gpio_EndCause] = turn.end_cause_id || 0;

	if (turn.end_cause_id) {
		pico8_gpio[gpio_TurnScore] = turn.score;
	}
}

function gpioUpdateScores() {
	pico8_gpio[gpio_NumPlayers] = md_game.players.length;
	var isPlayer = false;
	md_game.players.forEach((name, index) => {
		pico8_gpio[gpio_Scores + index] = md_game.scores[name];
		// Zero when player is currently not present in room
		pico8_gpio[gpio_TurnOrder + index] = playerNameToId(name);
		if (name === md_myName) {
			isPlayer = true;
		}
	});
	pico8_gpio[gpio_IsPlayer] = isPlayer;
}

function gpioUpdateCounters(phaseId, playerName) {
	pico8_gpio[gpio_TurnCounters] = md_game.round;
	pico8_gpio[gpio_TurnCounters + 1] = playerTurnOrder(playerName);
	console.info("Set turn to:", pico8_gpio[gpio_TurnCounters + 1]);
	pico8_gpio[gpio_TurnCounters + 3] = phaseId;
	gpioSetStr(gpio_ActivePlayerName, maxPlayerNameLength, playerName);
	const playerId = md_clients[playerName];
	pico8_gpio[gpio_ActivePlayerType] = (
		playerId
		? playerId
		: BEHAVIOUR_IDS[md_bots[playerName] || "unknown"] + 6
	);
}

function gpioGameEnd() {
	console.log("Writing game end", md_game);

	gpioUpdateCounters(gameEndId, md_game.winner);
	gpioUpdateScores();

	pico8_gpio[gpio_GameControl] = 1; // Ready to read
}

function gpioUpdateTurn(turn) {
	if (turn.phase === "Throwing" && turn.throw_count === 0) {
		md_game = md_gameNext;
	}

	gpioUpdateDice(turn.throw || {}, gpio_Throw);
	gpioUpdateDice(turn.side_dice || {}, gpio_SideDice);
	gpioUpdateTurnScore(turn);
	gpioUpdateScores();
	gpioUpdateCounters(PHASE_IDS[turn.phase], md_game.active_player);
	pico8_gpio[gpio_TurnCounters + 2] = turn.throw_count;

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

function gpioHandleChat() {
	if (pico8_gpio[gpio_ChatOut_Msg]) {
		md_socket.send(JSON.stringify({
			action: "chat",
			room_id: md_roomId,
			message_id: pico8_gpio[gpio_ChatOut_Msg]
		}));
		pico8_gpio[gpio_ChatOut_Msg] = 0;
	}

	if (md_gpioChats.length > 0 && !pico8_gpio[gpio_ChatIn_Msg]) {
		const chat = md_gpioChats[0];
		const senderId = md_clients[chat.sender];
		if (senderId) {
			console.info("Sending chat", chat.messageId, senderId);
			pico8_gpio[gpio_ChatIn_Msg] = chat.messageId;
			pico8_gpio[gpio_ChatIn_SenderId] = senderId;
			md_gpioChats = md_gpioChats.slice(1);
		} else {
			console.warn("Unknown sender", chat.sender);
		}
	}
}

function dump() {
	console.log("CTRL_IN_GAME  =", pico8_gpio[gpio_GameControl]);
	console.log("CTRL_IN_ROOM  =", pico8_gpio[gpio_RoomControl]);
	console.log("CTRL_OUT      =", pico8_gpio[gpio_OutControl]);
	console.log("ROOM_STATUS   =", pico8_gpio[gpio_RoomStatus]);
	console.log("ROOM          =", gpioGetStr(gpio_Room, 4));

	console.log("md_game =", md_game);
	console.log("md_gameNext =", md_gameNext);
	console.log("md_turnStates =", md_turnStates);
}

function gpioUpdate() {
	if (pico8_gpio[gpio_Handshake] === 7) {
		console.log("Pico-8 client started");
		pico8_gpio[gpio_Handshake] = 8;
	}

	gpioHandleRoomCommands();
	gpioHandleMove();
	gpioHandleChat();

	if (pico8_gpio[gpio_GameControl] == 0) {
		if (md_turnStates.length > 0) {
			const turnState = md_turnStates[0];

			md_turnStates = md_turnStates.slice(1);
			console.log("turnState =", turnState);

			if (md_turnStates.length === 0) {
				md_game = md_gameNext;
			}

			if (turnState) {
				gpioUpdateTurn(turnState);
			} else {
				md_gameEnded = true;
				gpioGameEnd();
			}

		}
	} else if (pico8_gpio[gpio_GameControl] == 5) {
		// Game start requested
		console.assert(isHost(), "Only host can start game");

		md_socket.send(JSON.stringify({
			action: "start-game",
			game_id: md_roomId,
			game_config: { bots: md_bots }
		}));

		pico8_gpio[gpio_GameControl] = 6; // Signal game starting
	}

	if (pico8_gpio[gpio_RoomControl] == 0) {
		if (md_gpioRoomBatch) {
			pico8_gpio[gpio_NumClients] = md_gpioRoomBatch.numClients;
			pico8_gpio[gpio_NumBots] = md_gpioRoomBatch.numBots;
			pico8_gpio[gpio_IsHost] = isHost() ? 1 : 0;
			md_gpioRoomBatch = null;

			pico8_gpio[gpio_RoomControl] = 4; // Signal start of batch
		} else if (md_gpioRoomUpdates.length > 0) {
			gpioRoomBatchUpdate(md_gpioRoomUpdates[0]);
			md_gpioRoomUpdates = md_gpioRoomUpdates.slice(1);

			pico8_gpio[gpio_RoomControl] = 1; // Signal ready to read
		}
	}
}

function md_update() {
	gpioUpdate();
	triggerBotMove();
}

window.setInterval(md_update, 30);
console.log("Loaded martian-dice.js");