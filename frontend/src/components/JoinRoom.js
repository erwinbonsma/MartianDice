import { GameRoom } from './GameRoom';
import { useState, useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function JoinRoom(props) {
	const [roomId, setRoomId] = useState();
	const [roomInput, setRoomInput] = useState('');
	const [joinError, setJoinError] = useState();

	const handleInputChange = (event) => {
		setRoomInput(event.target.value);
		setJoinError('');
	};

	const onCreateRoom = (event) => {
		console.log("onCreateRoom");

		const onMessage = (event) => {
			const msg = JSON.parse(event.data);
			console.log("onCreateRoom:", msg);

			if (msg.type === "response" && msg.status === "ok") {
				setRoomId(msg.game_id);
			}

			props.websocket.removeEventListener('message', onMessage);
		};
		props.websocket.addEventListener('message', onMessage);

		props.websocket.send(JSON.stringify({
			action: "create-game",
		}));
	}

	const onJoinRoom = (event) => {
		const onMessage = (event) => {
			const msg = JSON.parse(event.data);
			console.log("onJoinRoom:", msg);

			if (msg.type === "clients" && msg.game_id === roomInput) {
				setRoomId(msg.game_id);
			}
			if (msg.type === "response" && msg.status === "error") {
				setJoinError(msg.details);
			}

			props.websocket.removeEventListener('message', onMessage);
		};
		props.websocket.addEventListener('message', onMessage);

		props.websocket.send(JSON.stringify({
			action: "join-game",
			game_id: roomInput
		}));
	}
	
	return (
		roomId ? (
			<GameRoom roomId={roomId} playerName={props.playerName} websocket={props.websocket} />
		) : (<Container>
			<Row>
				<Col><Button onClick={onJoinRoom}>Join Room</Button></Col>
				<Col><input type="text" value={roomInput} onChange={handleInputChange} /></Col>
			</Row>
			{joinError && (
				<Row><Col as="p">Error: {joinError}</Col></Row>
			)}
			<Row><Col><Button onClick={onCreateRoom}>Create Room</Button></Col></Row>
		</Container>)
	)
}