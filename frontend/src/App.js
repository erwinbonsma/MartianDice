import './App.css';
import { JoinRoom } from './components/JoinRoom';
import { useState, useEffect } from 'react';

function App(props) {
	const [websocket, setWebsocket] = useState();

	useEffect(() => {
		if (!websocket) {
			// Create WebSocket connection.
			const socket = new WebSocket('ws://127.0.0.1:8765');

			// Connection opened
			socket.addEventListener('open', function (event) {
				setWebsocket(socket);
				socket.send(props.name);
			});

			const unsetSocket = () => { setWebsocket(undefined); }
			socket.addEventListener('close', unsetSocket);
			socket.addEventListener('error', unsetSocket);
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
			{ websocket && <JoinRoom websocket={websocket} playerName={props.name} /> }
		</div>
		</center>
	);
}

export default App;
