import { GameHeader } from './GameHeader';
import { GameSetup } from './GameSetup';
import { PlayArea } from './PlayArea';
import { PlayerList } from './PlayerList';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function GameRoom(props) {
	const [game, setGame] = useState();
	const [hostName, setHostName] = useState();
	const [clients, setClients] = useState([]);
	const [bots, setBots] = useState([]);
	const [transitionTurns, setTransitionTurns] = useState([]);

	useEffect(() => {
		// Listen for messages
		const onMessage = (event) => {
			const msg = JSON.parse(event.data);
			console.log(msg);
			switch (msg.type) {
				case "clients":
					setHostName(msg.host);
					setClients(msg.clients);
					break;
				case "bots":
					setBots(msg.bots);
					break;
				case "game-state":
					setTransitionTurns(msg.turn_state_transitions);
					setGame(msg.state);
					break;
				default:
					console.log("Unknown message", msg);
			}
		};
		
		console.log("addListener");
		props.websocket.addEventListener('message', onMessage);

		props.websocket.send(JSON.stringify({
			action: "send-status",
			game_id: props.gameId
		}));
    
		return function cleanup() {
			console.log("removeListener");
			props.websocket.removeEventListener('message', onMessage);
		}
	}, [props.websocket, props.gameId]);

	const onAddBot = () => {
		props.websocket.send(JSON.stringify({
			action: "add-bot",
			game_id: props.gameId,
			bot_behaviour: "smart"
		}));
	}
	const onRemoveBot = (e) => {
		props.websocket.send(JSON.stringify({
			action: "remove-bot",
			game_id: props.gameId,
			bot_name: e.target.id
		}));
	}
	const onStartGame = () => {
		props.websocket.send(JSON.stringify({
			action: "start-game",
			game_id: props.gameId
		}));
	}

	const turnState = transitionTurns.length > 0 ? transitionTurns[0] : game?.turn_state;
	const isAnimating = transitionTurns.length > 0;
	const isHost = (props.playerName === hostName);
	const myTurn = !isAnimating && (props.playerName === game?.active_player);
	const triggerBotMove = !isAnimating && isHost && bots.includes(game?.active_player);

	// Let host initiate bot moves
	useEffect(() => {
		if (triggerBotMove) {
			const delayedBotMove = setTimeout(() => {
				props.websocket.send(JSON.stringify({
					action: "bot-move",
					game_id: props.gameId
				}));
			}, 2000);

			return function cleanup() {
				clearTimeout(delayedBotMove);
			}
		}
	}, [triggerBotMove, props.gameId, props.websocket]);

	// Turn animations
	useEffect(() => {
		if (transitionTurns.length > 0) {
			const turnAnimation = setTimeout(() => {
				setTransitionTurns(transitionTurns.slice(1));
			}, 2000);

			return function cleanup() {
				clearTimeout(turnAnimation);
			}
		}
	}, [transitionTurns]);

	return (
		<Container>
			<Row><Col as="h5">Room {props.gameId}</Col></Row>
			<Row>
				<Col className="GameArea" sm={8}>
					<GameHeader game={game} turnState={turnState}></GameHeader>
					{ turnState &&
						<PlayArea gameId={props.gameId} turnState={turnState} websocket={props.websocket}
							myTurn={myTurn}></PlayArea>
					}
				</Col>
				<Col className="PlayersArea" sm={4}>
					{ !!game ? 
						<PlayerList players={game.players} scores={game.scores}></PlayerList> :
						<GameSetup clients={clients} bots={bots} 
							host={hostName} isHost={isHost}
							onAddBot={onAddBot} onRemoveBot={onRemoveBot}
							onStartGame={onStartGame}></GameSetup>
					}
				</Col>
			</Row>
		</Container>
	);
}