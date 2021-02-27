import './App.css';
import { AbductionZone } from './components/AbductionZone';
import { BattleZone } from './components/BattleZone';
import { DiceThrow } from './components/DiceThrow';
import { GameHeader } from './components/GameHeader';
import { GameSetup } from './components/GameSetup';
import { PlayerList } from './components/PlayerList';
import { useState, useEffect } from 'react';

function App(props) {
	const diceThrow = {"tank": 2, "ray": 3, "human": 1, "chicken": 1, "cow": 0};
	const earthlings = { "human": 2, "cow": 4 };
	const combatants = { tank: 3, ray: 2 };
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

	return (
    	<div className="App">
  			<div className="GameArea">
				<GameHeader game={game}></GameHeader>
				<DiceThrow throw={diceThrow}></DiceThrow>
				<BattleZone combatants={combatants}></BattleZone>
				<AbductionZone earthlings={earthlings}></AbductionZone>
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
