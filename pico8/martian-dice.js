const md_roomId = "PICO";

const gpio_RoomStatus = 3;

var md_joinAttempts = 0;
var md_bots = {};
var md_nextBotId = 0;
var md_game;
var md_transitionTurns = [];
var md_host;
var md_clients;
var md_socket;

function handleMessage(event) {
	const msg = JSON.parse(event.data);
	console.log("Message:", msg);
	switch (msg.type) {
		case "clients":
			md_clients = msg.clients;
			md_host = msg.host;
			if (pico8_gpio[gpio_RoomStatus] == 1) {
				// Signal that room was joined successfully;
				pico8_gpio[gpio_RoomStatus] = 2;
			}
			break;
		case "game-config":
			md_bots = msg.game_config.bots;
			md_nextBotId = msg.game_config.next_bot_id;
			break;
		case "game-state":
			if (md_game && md_game.id !== msg.state.prev_id) {
				console.warn(`Unexpected state transition: ${md_game.id} != ${msg.state.prev_id}`);
			}
			md_transitionTurns = msg.turn_state_transitions;
			md_game = msg.state;
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

function gpioUpdate() {
	if (pico8_gpio[gpio_RoomStatus] == 1) {
		console.log("Initiating room join");
		connectToServer(joinRoom);
	}
	if (pico8_gpio[gpio_RoomStatus] == 3) {
		console.log("Initiating room exit");
		leaveRoom();
	}
}

window.setInterval(gpioUpdate, 30);