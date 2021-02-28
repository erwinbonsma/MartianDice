import './App.css';
import { GameHeader } from './components/GameHeader';
import { GameSetup } from './components/GameSetup';
import { PlayArea } from './components/PlayArea';
import { PlayerList } from './components/PlayerList';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

function App(props) {
	const [websocket, setWebsocket] = useState();
	const [game, setGame] = useState();
	const [clients, setClients] = useState([]);
	const [bots, setBots] = useState([]);
	const [host, setHost] = useState();

	useEffect(() => {
		if (!websocket) {
			// Create WebSocket connection.
			const socket = new WebSocket('ws://127.0.0.1:8765');

			// Connection opened
			socket.addEventListener('open', function (event) {
				setWebsocket(socket);
    			socket.send(props.name);
			});

			// Listen for messages
			socket.addEventListener('message', function (event) {
				const msg = JSON.parse(event.data);
    			console.log('Message from server ', msg);
				switch (msg.type) {
					case "clients":
						setHost(msg.host);
						setClients(msg.clients);
						break;
					case "bots":
						setBots(msg.bots);
						break;
					case "game-state":
						setGame(msg);
						break;
					default:
						console.log("Unknown message", msg.type);
				}
			});
		}
    
		return function cleanup() {
			if (websocket) {
				websocket.close();
			}
		}
	}, [props.name, websocket]);

	useEffect(() => {
		const testGame = {
			active_player: "Bob",
			players: ["Alice", "Bob", props.name],
			round: 1, 
			score: { "Alice": 3, "Bob": 5, [props.name]: 2},
			done: false,
			turn_state: {
				phase: "Thrown",
				//throw: { Ray: 4, Tank: 3, Chicken: 2, Human: 1},
				throw: { Ray: 3, Chicken: 2},
				throw_count: 2,
				side_dice: { Tank: 1, Cow: 2},
			}
		}

		//setGame(testGame);
	}, [props.name]);

	const onAddBot = () => {
		websocket.send(JSON.stringify({
			action: "add-bot",
			bot_behaviour: "smart"
		}));
	}
	const onRemoveBot = (e) => {
		websocket.send(JSON.stringify({
			action: "remove-bot",
			bot_name: e.target.id
		}));
	}
	const onStartGame = () => {
		websocket.send(JSON.stringify({
			action: "start-game"
		}));
	}

	return (
		<center>
    	<Container className="App">
			<Row><Col as="h1">Martian Dice</Col></Row>
			<Row>
  				<Col className="GameArea" sm={8}>
					<GameHeader game={game}></GameHeader>
					{ game?.turn_state &&
						<PlayArea game={game} websocket={websocket}
							my_turn={props.name === game.active_player}></PlayArea>
					}
				</Col>
				<Col className="PlayersArea" sm={4}>
					{ !!game ? 
						<PlayerList players={game.players} scores={game.score}></PlayerList> :
						<GameSetup clients={clients} bots={bots} 
							host={host} isHost={host === props.name}
							onAddBot={onAddBot} onRemoveBot={onRemoveBot}
							onStartGame={onStartGame}></GameSetup>
					}
				</Col>
			</Row>
		</Container>
		</center>
	);
}

export default App;
