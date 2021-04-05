const playerName = "Pico-8";

function connectToServer() {
	console.log("Connecting to server");

	const ws = new WebSocket("ws://127.0.0.1:8765");
	ws.addEventListener('open', function (event) {
		console.log("Opened websocket");

		ws.send(JSON.stringify({
			action: "join-room",
			room_id: "PICO",
			client_id: playerName
		}));
	});
}

window.onload = connectToServer;