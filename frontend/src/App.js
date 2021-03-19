import './App.css';
import { Die } from './components/Die';
import { JoinRoom } from './components/JoinRoom';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

function App(props) {
	const [websocket, setWebsocket] = useState();
	const [nameInput, setNameInput] = useState('');
	const [playerName, setPlayerName] = useState();
	const [roomId, setRoomId] = useState();
	const [errorMessage, setErrorMessage] = useState();

	useEffect(() => {
		if (!websocket) {
			// Create WebSocket connection.
			//const socket = new WebSocket('wss://gv9b6yzx3j.execute-api.eu-west-1.amazonaws.com/dev');
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
		event.preventDefault();

		setPlayerName(nameInput);
	}

	const onLogout = (event) => {
		if (roomId) {
			onRoomExit();
		}

		setPlayerName(undefined);
	}

	const onRoomJoined = (roomId) => {
		setRoomId(roomId);
	}
	const onRoomExit = () => {
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
						<Button variant="outline-secondary" size="xs" onClick={onLogout}>logout</Button>
					</center>)}</Col>
					<Col xs={4} sm={8} as="h1" className="TableHeader"
						style={{color: "black", display: "flex", justifyContent: "space-between", alignItems: "center"}}>
						<Die face="tank" />
						<h1 className="d-none d-md-block">Martian Dice</h1>
						<Die face="ray" />
					</Col>
					<Col xs={4} sm={2}>{roomId && (<center>
						Room {roomId} <br/>
						<Button  variant="outline-secondary" size="xs" onClick={onRoomExit}>leave</Button>
					</center>)}
					</Col>
				</Row>
			</Container>
			{ playerName ? (
				<JoinRoom websocket={websocket} playerName={playerName} roomId={roomId}
					onRoomJoined={onRoomJoined} />
			) : (
				<Container><Row>
					<Col xl={3} lg={2} md={1} />
					<Col>
						<p>What name would you like to use today?</p>
						<form onSubmit={onEnterName} style={{display: "flex"}}>
							<div>Name:</div>
							<div style={{flex: "1"}} />
							<input size={20} type="text" value={nameInput} onChange={handleInputChange} />
							<div style={{flex: "2"}} />
							<Button type="submit" disabled={nameInput === '' || nameInput.length > 12} >OK</Button>
							<div style={{flex: "10"}} />
						</form>
						{ errorMessage &&
							<p className="Error">{errorMessage}</p>
						}
					</Col>
					<Col xl={3} lg={2} md={1} />
				</Row></Container>
			)}
		</div>
		</center>
	);
}

export default App;
