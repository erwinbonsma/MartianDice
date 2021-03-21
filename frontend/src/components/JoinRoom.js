import { GameRoom } from './GameRoom';
import { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function JoinRoom(props) {
	const [roomInput, setRoomInput] = useState('');
	const [errorMessage, setErrorMessage] = useState();

	const handleInputChange = (event) => {
		setRoomInput(event.target.value);
		setErrorMessage('');
	};

	const joinRoom = (roomId) => {
		const handleMessage = (event) => {
			const msg = JSON.parse(event.data);

			if (msg.type === "clients" && msg.game_id === roomId) {
				props.onRoomJoined(msg.game_id);
			}
			if (msg.type === "response" && msg.status === "error") {
				setErrorMessage(msg.details);
			}

			props.websocket.removeEventListener('message', handleMessage);
		};
		props.websocket.addEventListener('message', handleMessage);

		// Clear any lingering error message from previous attempt
		setErrorMessage('');

		props.websocket.send(JSON.stringify({
			action: "join-room",
			game_id: roomId,
			client_id: props.playerName
		}));
	}

	const handleJoinRoom = () => { joinRoom(roomInput); }
	
	const handleCreateRoom = () => {
		const handleMessage = (event) => {
			const msg = JSON.parse(event.data);

			if (msg.type === "response" && msg.status === "ok") {
				// Set input so that you can easily return after accidentally leaving the room
				setRoomInput(msg.room_id);

				joinRoom(msg.room_id);
			}

			props.websocket.removeEventListener('message', handleMessage);
		};
		props.websocket.addEventListener('message', handleMessage);

		props.websocket.send(JSON.stringify({
			action: "create-room",
		}));
	}

	return (
		props.roomId ? (
			<GameRoom roomId={props.roomId} playerName={props.playerName} websocket={props.websocket} />
		) : (
		<Container><Row>
			<Col lg={3} md={2} />
			<Col>
				<h4>Please proceed to a room</h4><br />
				<Container><Row>
					<Col xs="auto">Join room</Col>
					<Col><input type="text" value={roomInput} onChange={handleInputChange} size={6} /></Col>
					<Col xs={4} sm={3}>
						<Button style={{width: "100%"}} disabled={roomInput.length !== 4} onClick={handleJoinRoom}>Join</Button>
					</Col>
				</Row></Container>
				{ errorMessage &&
					<p className="Error">{errorMessage}</p>
				}
				<br />
				<Container><Row>
					<Col as="p">Create new room</Col>
					<Col xs={4} sm={3}>
						<Button style={{width: "100%"}} onClick={handleCreateRoom}>Create</Button>
					</Col>
				</Row></Container>
			</Col>
			<Col lg={3} md={2} />
		</Row></Container>
	));
}