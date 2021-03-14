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
			action: "join-room",
			game_id: roomId,
			client_id: props.playerName
		}));
	}

	const onJoinRoom = () => { joinRoom(roomInput); }
	
	const onCreateRoom = () => {
		console.log("onCreateRoom");

		const onMessage = (event) => {
			const msg = JSON.parse(event.data);
			console.log("onCreateRoom:", msg);

			if (msg.type === "response" && msg.status === "ok") {
				joinRoom(msg.room_id);
			}

			props.websocket.removeEventListener('message', onMessage);
		};
		props.websocket.addEventListener('message', onMessage);

		props.websocket.send(JSON.stringify({
			action: "create-room",
		}));
	}

	return (
		roomId ? (
			<GameRoom roomId={roomId} playerName={props.playerName} websocket={props.websocket} />
		) : (
		<Container><Row>
			<Col lg={3} md={2} />
			<Col>
				<p>Welcome {props.playerName}!</p>
				<p>Please proceed to a room:</p>
				<Container><Row>
					<Col xs="auto">Join room</Col>
					<Col><input type="text" value={roomInput} onChange={handleInputChange} size={6} /></Col>
					<Col xs={3}><Button style={{width: "100%"}} disabled={roomInput.length !== 4} onClick={onJoinRoom}>Join</Button></Col>
				</Row></Container>
				{ errorMessage &&
					<p className="Error">{errorMessage}</p>
				}
				<br />
				<Container><Row>
					<Col as="p">Create new room</Col>
					<Col xs={3}><Button style={{width: "100%"}} onClick={onCreateRoom}>Create</Button></Col>
				</Row></Container>
				<center><Button onClick={props.onLogout}>Log out</Button></center>
			</Col>
			<Col lg={3} md={2} />
		</Row></Container>
	));
}