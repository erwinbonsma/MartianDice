import './App.css';
import { GameRoom } from './components/GameRoom';
import { useState, useEffect } from 'react';

function App(props) {
	const [websocket, setWebsocket] = useState();
	const [gameId, setGameId] = useState();

	useEffect(() => {
		if (!websocket) {
			// Create WebSocket connection.
			const socket = new WebSocket('ws://127.0.0.1:8765');

			const onMessage = (event) => {
				const msg = JSON.parse(event.data);
				console.log('Message from server ', msg);
				if (msg.type === "response") {
					if (msg.status !== "ok") {
						console.log("Error:", msg);
					} else if (msg.game_id) {
						setGameId(msg.game_id);
						socket.removeEventListener('message', onMessage);
					}
				}
			};

			// Listen for messages
			socket.addEventListener('message', onMessage); 

			// Connection opened
			socket.addEventListener('open', function (event) {
				setWebsocket(socket);
    			socket.send(props.name);
				socket.send(JSON.stringify({
					action: "create-game"
				}));
			});
		}
    
		return function cleanup() {
			if (websocket) {
				websocket.close();
			}
		}
	}, [props.name, websocket]);

	return (
		<center>
    	<div className="App">
			<h1>Martian Dice</h1>
			{gameId && 
				<GameRoom gameId={gameId} playerName={props.name} websocket={websocket}></GameRoom>
			}
		</div>
		</center>
	);
}

export default App;
