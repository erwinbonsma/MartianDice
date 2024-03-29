import { GameRoom } from './GameRoom';
import { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

const AUDIO_URLS = {
	Chicken: "kip.mp3",
	Cow: "cow.mp3",
	Human: "huh.mp3",
	Ray: "ray.mp3",
	Success: "win.mp3",
	Fail: "die.mp3"
};

export function JoinRoom({ roomId, playerName, websocket, onRoomJoined }) {
	const [roomInput, setRoomInput] = useState('');
	const [enableSound, setEnableSound] = useState(true);
	const [errorMessage, setErrorMessage] = useState();
	const [joinCount, setJoinCount] = useState(0);
	const [audioTracks, setAudioTracks] = useState();

	const handleInputChange = (event) => {
		setRoomInput(event.target.value.toUpperCase());
		setErrorMessage('');
	};

	const joinRoom = (roomToJoin) => {
		const handleMessage = (event) => {
			const msg = JSON.parse(event.data);

			if (msg.type === "clients" && msg.room_id === roomToJoin) {
				onRoomJoined(msg.room_id);
			}
			if (msg.type === "response" && msg.status === "error") {
				setErrorMessage(msg.details);
			}

			websocket.removeEventListener('message', handleMessage);
		};
		websocket.addEventListener('message', handleMessage);

		// Clear any lingering error message from previous attempt
		setErrorMessage('');

		setJoinCount(joinCount + 1);

		websocket.send(JSON.stringify({
			action: "join-room",
			room_id: roomToJoin,
			client_id: playerName
		}));
	}

	const initAudioTracks = () => {
		if (audioTracks) {
			return;
		}

		const tracks = Object.entries(AUDIO_URLS).reduce(
			(dict, [key, url]) => {
				dict[key] = new Audio(url);
				return dict;
			}, {});

		// Many browsers require user interaction before audio can be played. So when user clicks
		// button, initialise all audio tracks by playing them (with zero volume).
		Object.entries(tracks).forEach(([key, audio]) => {
			const origVolume = audio.volume;
			const playPromise = audio.play();
			audio.volume = 0;
			if (playPromise) {
				playPromise.then(_ => {
					audio.pause();
					audio.volume = origVolume;
					audio.currentTime = 0;
				})
				.catch(error => {
					console.error(`Failed to play/pause ${key}: ${error}`);
				});
			}
		});

		setAudioTracks(tracks);
	}

	const handleJoinRoom = () => {
		initAudioTracks();
		joinRoom(roomInput);
	}

	const handleSoundToggle = () => {
		setEnableSound(!enableSound);
	}
	
	const handleCreateRoom = () => {
		initAudioTracks();

		const handleMessage = (event) => {
			const msg = JSON.parse(event.data);

			if (msg.type === "response" && msg.status === "ok") {
				// Set input so that you can easily return after accidentally leaving the room
				setRoomInput(msg.room_id);

				joinRoom(msg.room_id);
			}

			websocket.removeEventListener('message', handleMessage);
		};
		websocket.addEventListener('message', handleMessage);

		websocket.send(JSON.stringify({
			action: "create-room",
		}));
	}

	return (
		roomId ? (
			<GameRoom roomId={roomId} playerName={playerName} instanceId={joinCount}
				audioTracks={audioTracks} enableSound={enableSound} websocket={websocket} />
		) : (
		<Container><Row>
			<Col lg={3} md={2} />
			<Col>
				<Container>
					<Row className="FormRow"><Col as="h4">Please proceed to a room</Col></Row>
					<Row className="FormRow">
						<Col xs="auto">Join room</Col>
						<Col><input type="text" value={roomInput} onChange={handleInputChange} size={6} /></Col>
						<Col xs={4} sm={3}>
							<Button style={{width: "100%"}} disabled={roomInput.length !== 4} onClick={handleJoinRoom}>Join</Button>
						</Col>
					</Row>
					{ errorMessage &&
						<Row className="FormRow"><Col as="p" className="Error">{errorMessage}</Col></Row>
					}
					<Row className="FormRow">
						<Col as="p">Create new room</Col>
						<Col xs={4} sm={3}>
							<Button style={{width: "100%"}} onClick={handleCreateRoom}>Create</Button>
						</Col>
					</Row>
					<Row className="FormRow">
						<Col as="label" htmlFor="soundToggle">Sound effects</Col>
						<Col xs={4} sm={3}>
							<center><input type="checkbox" name="sound" id="soundToggle"
								checked={enableSound} onChange={handleSoundToggle} /></center>
						</Col>
					</Row>
				</Container>
			</Col>
			<Col lg={3} md={2} />
		</Row></Container>
	));
}