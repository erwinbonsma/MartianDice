import { GameRoom } from './GameRoom';
import { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function JoinRoom(props) {
	const [roomId, setRoomId] = useState();
	const [roomInput, setRoomInput] = useState('');
	const [errorMessage, setErrorMessage] = useState();

	const handleInputChange = (event) => {
		setRoomInput(event.target.value);
		setErrorMessage('');
	};

	const joinRoom = (roomId) => {
		const onMessage = (event) => {
			const msg = JSON.parse(event.data);
			console.log("onJoinRoom:", msg);

			if (msg.type === "clients" && msg.game_id === roomId) {
				setRoomId(msg.game_id);
			}
			if (msg.type === "response" && msg.status === "error") {
				setErrorMessage(msg.details);
			}

			props.websocket.removeEventListener('message', onMessage);
		};
		props.websocket.addEventListener('message', onMessage);

		props.websocket.send(JSON.stringify({
			action: "join-game",
			game_id: roomId
		}));
	}

	const onJoinRoom = () => { joinRoom(roomInput); }
	
	const onCreateRoom = () => {
		console.log("onCreateRoom");

		const onMessage = (event) => {
			const msg = JSON.parse(event.data);
			console.log("onCreateRoom:", msg);

			if (msg.type === "response" && msg.status === "ok") {
				joinRoom(msg.game_id);
			}

			props.websocket.removeEventListener('message', onMessage);
		};
		props.websocket.addEventListener('message', onMessage);

		props.websocket.send(JSON.stringify({
			action: "create-game",
		}));
	}

	return (
		roomId ? (
			<GameRoom roomId={roomId} playerName={props.playerName} websocket={props.websocket} />
		) : (
			<Container><Row>
			<Col xl={3} lg={2} md={1} />
			<Col>
				<p>Welcome {props.playerName}!</p>
				<p>Please proceed to join an existing room:</p>
				<Container><Row>
					<Col xs="auto">Room:</Col>
					<Col><input type="text" value={roomInput} onChange={handleInputChange} /></Col>
					<Col xs={2}><Button style={{width: "100%"}} disabled={roomInput === ''} onClick={onJoinRoom}>OK</Button></Col>
				</Row></Container>
				{ errorMessage &&
					<p className="Error">{errorMessage}</p>
				}
				<br />
				<p>Or create a new one:</p>
				<center><Button onClick={onCreateRoom}>Create Room</Button></center>
			</Col>
			<Col xl={3} lg={2} md={1} />
		</Row></Container>
	));
}