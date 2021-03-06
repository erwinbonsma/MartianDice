import './App.css';
import { JoinRoom } from './components/JoinRoom';
import { useState, useEffect } from 'react';
import Button from 'react-bootstrap/Button';

function App(props) {
	const [websocket, setWebsocket] = useState();
	const [nameInput, setNameInput] = useState('');
	const [playerName, setPlayerName] = useState();
	const [errorMessage, setErrorMessage] = useState();

	useEffect(() => {
		if (!websocket) {
			// Create WebSocket connection.
			const socket = new WebSocket('ws://127.0.0.1:8765');

			// Connection opened
			socket.addEventListener('open', function (event) {
				setWebsocket(socket);
			});

			const unsetSocket = () => { setWebsocket(undefined); }
			socket.addEventListener('close', unsetSocket);
			socket.addEventListener('error', unsetSocket);
		}
    
		return function cleanup() {
			if (websocket) {
				console.log("Closing websocket");
				websocket.close();
			}
		}
	}, [websocket]);

	const handleInputChange = (event) => {
		setNameInput(event.target.value);
		setErrorMessage('');
	};

	const onEnterName = (event) => {
		const onMessage = (event) => {
			const msg = JSON.parse(event.data);
			console.log("onEnterName:", msg);

			if (msg.type === "response") {
				if (msg.status === "error") {
					setErrorMessage(msg.details);
				} else {
					setPlayerName(msg.client_id);
				}
			}

			websocket.removeEventListener('message', onMessage);
		};
		websocket.addEventListener('message', onMessage);

		websocket.send(JSON.stringify({
			action: "join",
			client_id: nameInput
		}));
	}

	return (
		<center>
    	<div className="App">
			<h1>Martian Dice</h1>
			{ playerName ?
				<JoinRoom websocket={websocket} playerName={playerName} /> :
				<p>Player name:
					<input type="text" value={nameInput} onChange={handleInputChange} />
					{ errorMessage && `Error: ${errorMessage}` }
					<Button disabled={nameInput === ''} onClick={onEnterName}>OK</Button>
				</p>
			}
		</div>
		</center>
	);
}

export default App;
