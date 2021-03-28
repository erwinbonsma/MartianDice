import './App.css';
import { Die } from './components/Die';
import { JoinRoom } from './components/JoinRoom';
import config from './utils/config';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

function App() {
	const [websocket, setWebsocket] = useState();
	const [nameInput, setNameInput] = useState('');
	const [playerName, setPlayerName] = useState();
	const [roomId, setRoomId] = useState();
	const [errorMessage, setErrorMessage] = useState();

	useEffect(() => {
		if (websocket || !playerName) {
			// Only set up websocket after registration
			return
		}

		// Create WebSocket connection.
		const socket = new WebSocket(config.SERVICE_ENDPOINT);

		// Connection opened
		socket.addEventListener('open', function (event) {
			console.log("Opened websocket");
			setWebsocket(socket);
		});

		const unsetSocket = () => {
			setErrorMessage("Disconnected from server");
			setWebsocket(undefined);
		}
		socket.addEventListener('close', unsetSocket);
		socket.addEventListener('error', unsetSocket);
    
		return function cleanup() {
			if (websocket) {
				console.log("Closing websocket");
				setWebsocket(undefined);
				websocket.close();
			}
		}
	}, [websocket, playerName]);

	const handleInputChange = (event) => {
		setNameInput(event.target.value);
		setErrorMessage('');
	};

	const handleRegistration = (event) => {
		event.preventDefault();

		setPlayerName(nameInput);
	}

	const handleLogout = (event) => {
		if (roomId) {
			handleRoomExit();
		}

		setPlayerName(undefined);

		// Few lines of duplicated code with useEffect, but seems hard/awkward to avoid 
		console.log("Closing websocket");
		setWebsocket(undefined);
		websocket.close();	}

	const handleRoomEntry = (roomId) => {
		setRoomId(roomId);
	}
	const handleRoomExit = () => {
		websocket.send(JSON.stringify({
			action: "leave-room",
			game_id: roomId
		}));

		setRoomId(undefined);
	}

	return (
		<center>
    	<div className="App">
			<Container>
				<Row>
					<Col xs={4} sm={2}>{playerName && (<center>
						{playerName} <br/>
						<Button variant="outline-secondary" size="xs" onClick={handleLogout}>logout</Button>
					</center>)}</Col>
					<Col xs={4} sm={8} className="AppHeader"
						style={{display: "flex", justifyContent: "space-between", alignItems: "center" }}>
						<Die face="tank" />
						<h1 className="d-none d-md-block">Martian Dice</h1>
						<Die face="ray" />
					</Col>
					<Col xs={4} sm={2}>{roomId && (<center>
						Room {roomId} <br/>
						<Button  variant="outline-secondary" size="xs" onClick={handleRoomExit}>leave</Button>
					</center>)}
					</Col>
				</Row>
			</Container>
			{ playerName ? (
				websocket ? (
					<JoinRoom websocket={websocket} playerName={playerName} roomId={roomId}
						onRoomJoined={handleRoomEntry} />
				) : <center><p className="Error">Failed to connect to server</p></center>
			) : (
				<Container><Row>
					<Col lg={3} md={2} sm={1} />
					<Col lg={6} md={8} sm={10} >
						<center>
						<h4>Registration</h4>
						<p>Who will be captaining your Martian fleet?</p>
						<form onSubmit={handleRegistration} style={{ display: "flex" }}>
							<div>Name:</div>
							<div style={{flex: "1"}} />
							<input size={20} type="text" value={nameInput} onChange={handleInputChange} />
							<div style={{flex: "2"}} />
							<Button type="submit" disabled={nameInput === '' || nameInput.length > 12} >OK</Button>
						</form>
						{ errorMessage &&
							<p className="Error">{errorMessage}</p>
						}
						</center>
					</Col>
					<Col lg={3} md={2} sm={1} />
				</Row></Container>
			)}
		</div>
		</center>
	);
}

export default App;
