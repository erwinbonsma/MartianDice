import { Chat } from './Chat';
import { GameHeader } from './GameHeader';
import { GameSetup } from './GameSetup';
import { PlayArea } from './PlayArea';
import { PlayerList } from './PlayerList';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function GameRoom(props) {
	// The future game is the latest game from the service. However, due to client-side animation
	// delays, it takes some time before this becomes the game state that is displayed.
	const [futureGame, setFutureGame] = useState();
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
					setFutureGame(msg.state);
					break;
				default:
					console.log("Unknown message", msg);
			}
		};
		
		console.log("addListener");
		props.websocket.addEventListener('message', onMessage);

		props.websocket.send(JSON.stringify({
			action: "send-status",
			game_id: props.roomId
		}));
    
		return function cleanup() {
			console.log("removeListener");
			props.websocket.removeEventListener('message', onMessage);
		}
	}, [props.websocket, props.roomId]);

	const onAddBot = () => {
		props.websocket.send(JSON.stringify({
			action: "add-bot",
			game_id: props.roomId,
			bot_behaviour: "smart"
		}));
	}
	const onRemoveBot = (e) => {
		props.websocket.send(JSON.stringify({
			action: "remove-bot",
			game_id: props.roomId,
			bot_name: e.target.id
		}));
	}
	const onStartGame = () => {
		props.websocket.send(JSON.stringify({
			action: "start-game",
			game_id: props.roomId
		}));
	}

	const turnState = transitionTurns.length > 0 ? transitionTurns[0] : futureGame?.turn_state;
	const isAnimating = transitionTurns.length > 0;
	const isHost = (props.playerName === hostName);
	const myTurn = !isAnimating && (props.playerName === futureGame?.active_player);
	const triggerBotMove = !isAnimating && isHost && bots.includes(futureGame?.active_player);

	// Let host initiate bot moves
	useEffect(() => {
		if (triggerBotMove) {
			const delayedBotMove = setTimeout(() => {
				props.websocket.send(JSON.stringify({
					action: "bot-move",
					game_id: props.roomId
				}));
			}, 2000);

			return function cleanup() {
				clearTimeout(delayedBotMove);
			}
		}
	}, [triggerBotMove, props.roomId, props.websocket]);

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

	useEffect(() => {
		if (
			(turnState?.throw_count === 0 && turnState?.phase === "Throwing") ||
			transitionTurns.length === 0
		) {
			setGame(futureGame);
		}
	}, [turnState, futureGame, transitionTurns.length]);

	const offlinePlayers = game
		? game.players.filter(player => !(bots.includes(player) || clients.includes(player)))
		: [];

	return (
		<Container>
			<Row><Col as="h5">Room {props.roomId}</Col></Row>
			<Row style={{height: "80vh", background: "green"}}>
				<Col className="GameArea" sm={8}>
					<GameHeader game={game} turnState={turnState}></GameHeader>
					{ turnState &&
						<PlayArea gameId={props.roomId} turnState={turnState} websocket={props.websocket}
							myTurn={myTurn}></PlayArea>
					}
				</Col>
				<Col className="PlayersArea" sm={4}>
					{ !!game ? 
						<PlayerList players={game.players} scores={game.scores} activePlayer={game.active_player}
							offlinePlayers={offlinePlayers}></PlayerList> :
						<GameSetup clients={clients} bots={bots} 
							host={hostName} isHost={isHost}
							onAddBot={onAddBot} onRemoveBot={onRemoveBot}
							onStartGame={onStartGame}></GameSetup>
					}
					<Chat websocket={props.websocket} roomId={props.roomId} />
				</Col>
			</Row>
		</Container>
	);
}