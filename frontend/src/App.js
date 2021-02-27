import './App.css';
import { AbductionZone } from './components/AbductionZone';
import { BattleZone } from './components/BattleZone';
import { DiceThrow } from './components/DiceThrow';
import { GameHeader } from './components/GameHeader';
import { GameSetup } from './components/GameSetup';
import { PlayerList } from './components/PlayerList';
import { useState, useEffect } from 'react';

function App(props) {
	const players = ["Alice", "Bob", "Charlie"];
	const scores = {"Alice": 7, "Bob": 4, "Charlie": 5};
	
	const [ws, setWebsocket] = useState();
	const [game, setGame] = useState();
	const [clients, setClients] = useState([]);
	const [bots, setBots] = useState([]);
	const [host, setHost] = useState();

	useEffect(() => {
		if (!ws) {
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
			if (ws) {
				ws.close();
			}
		}
	}, [props.name, ws]);

	const onAddBot = () => {
		ws.send(JSON.stringify({
			action: "add-bot",
			bot_behaviour: "random"
		}));
	}
	const onRemoveBot = (e) => {
		ws.send(JSON.stringify({
			action: "remove-bot",
			bot_name: e.target.id
		}));
	}
	const onStartGame = () => {
		ws.send(JSON.stringify({
			action: "start-game"
		}));
	}

	let gameZone;
	if (game) {
		const diceThrow = game.turn_state.throw || {};
		const earthlings = {}
		const combatants = {}
		Object.entries(game.turn_state.side_dice).forEach(([die, number]) => {
			if (die === "Tank" || die === "Ray") {
				combatants[die] = number;
			} else {
				earthlings[die] = number;
			}
		});
		console.log("diceThrow", diceThrow);
		console.log("earthlings", earthlings);
		console.log("combatants", combatants);
		gameZone = (
			<div>
				<DiceThrow throw={diceThrow}></DiceThrow>
				<BattleZone combatants={combatants}></BattleZone>
				<AbductionZone earthlings={earthlings}></AbductionZone>
			</div>
		)
	}

	return (
    	<div className="App">
  			<div className="GameArea">
				<GameHeader game={game}></GameHeader>
				{ gameZone }
			</div>
			<div className="PlayersArea">
				{ !!game ? 
					<PlayerList players={players} scores={scores}></PlayerList> :
					<GameSetup clients={clients} bots={bots} 
						host={host} isHost={host === props.name}
						onAddBot={onAddBot} onRemoveBot={onRemoveBot}
						onStartGame={onStartGame}></GameSetup>
				}
			</div>
		</div>
	);
}

export default App;
