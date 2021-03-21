import { Chat } from './Chat';
import { GameHeader } from './GameHeader';
import { GameResult } from './GameResult';
import { GameRules } from './GameRules';
import { GameSetup } from './GameSetup';
import { PlayArea } from './PlayArea';
import { PlayerList } from './PlayerList';
import React from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export class GameRoom extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			// The future game is the latest game from the service. However, due to client-side animation
			// delays, it takes some time before this becomes the game state that is displayed.
			futureGame: undefined,
			game: undefined,
			hostName: undefined,
			clients: [],
			bots: [],
			transitionTurns: [],
			isAnimating: false
		};

		this.handleAddBot = this.handleAddBot.bind(this);
		this.handleRemoveBot = this.handleRemoveBot.bind(this);
		this.handleStartGame = this.handleStartGame.bind(this);
		this.handleAnimationChange = this.handleAnimationChange.bind(this);
		this.handleMessage = this.handleMessage.bind(this);
	}

	get isReplaying() {
		return this.state.transitionTurns.length > 0;
	}
	get isHost() {
		return this.props.playerName === this.state.hostName;
	}
	get myTurn() {
		return !this.isReplaying && (this.props.playerName === this.state.futureGame?.active_player);
	}
	get turnState() {
		return this.state.transitionTurns.length > 0
			? this.state.transitionTurns[0]
			: this.state.futureGame?.turn_state;
	}

	handleAddBot(event) {
		this.props.websocket.send(JSON.stringify({
			action: "add-bot",
			game_id: this.props.roomId,
			bot_behaviour: event
		}));
	}

	handleRemoveBot(event) {
		this.props.websocket.send(JSON.stringify({
			action: "remove-bot",
			game_id: this.props.roomId,
			bot_name: event.target.id
		}));
	}

	handleStartGame() {
		this.props.websocket.send(JSON.stringify({
			action: "start-game",
			game_id: this.props.roomId
		}));
	}

	handleAnimationChange(flag) {
		console.log("GameRoom.isAnimating =", flag);
		if (flag !== this.state.isAnimating) {
			this.setState({
				isAnimating: flag
			});
		}
	}

	handleMessage(event) {
		const msg = JSON.parse(event.data);
		console.log(msg);
		switch (msg.type) {
			case "clients":
				this.setState({
					hostName: msg.host,
					clients: msg.clients
				});
				break;
			case "bots":
				this.setState({
					bots: msg.bots
				});
				break;
			case "game-state":
				this.setState({
					transitionTurns: msg.turn_state_transitions,
					futureGame: msg.state
				});
				break;
			default:
				console.log("Unknown message", msg);
		}
	}

	animateTransitions() {
		if (this.turnAnimation) {
			console.log("Animation already scheduled");
			return;
		}

		if (this.state.transitionTurns.length === 0) {
			console.log("No transitions");
			return;
		}
		if (this.state.isAnimating) {
			console.log("skipping transitions while animating");
			return;
		}

		this.turnAnimation = setTimeout(() => {
			// Finished animating current transition. Move to the next
			this.setState((state) => ({
				transitionTurns: state.transitionTurns.slice(1)
			}));
			console.log("performed transition");
		}, 10000);
	}

	triggerBotMove() {
		if (this.botMoveTrigger) {
			// Event trigger already scheduled
			return;
		}

		if (
			this.isReplaying ||
			!this.isHost ||
			!this.state.bots.includes(this.state.futureGame?.active_player)
		) {
			// Bot move does not require triggering (yet)
			return;
		}
		
		this.botMoveTrigger = setTimeout(() => {
			this.props.websocket.send(JSON.stringify({
				action: "bot-move",
				game_id: this.props.roomId
			}));
		}, 2000);
	}

	updateGame() {
		if (this.state.game === this.state.futureGame) {
			return;
		}

		if (
			// Update game state when replay animations have caught up
			!this.isReplaying ||
			// or after the active player changed (so that scores and turn meta-data are accurate)
			(this.turnState?.throw_count === 0 && this.turnState?.phase === "Throwing")
		) {
			this.setState({
				game: this.state.futureGame
			});
		}
	}

	componentDidMount() {
		this.props.websocket.addEventListener('message', this.handleMessage);

		this.props.websocket.send(JSON.stringify({
			action: "send-status",
			game_id: this.props.roomId
		}));
	}
  
	componentWillUnmount() {
		this.props.websocket.removeEventListener('message', this.handleMessage);

		if (this.turnAnimation) {
			console.log("stopping turn animation");
			clearTimeout(this.turnAnimation);
			this.turnAnimation = undefined;
		}

		if (this.botMoveTrigger) {
			clearTimeout(this.botMoveTrigger);
			this.botMoveTrigger = undefined;
		}
	}

	componentDidUpdate() {
		this.animateTransitions();
		this.triggerBotMove();
		this.updateGame();
	}

	render() {
		const game = this.state.game;
		const turnState = this.turnState;

		console.log("turnState =", turnState);

		const offlinePlayers = game
			? game.players.filter(
				player => !(this.state.bots.includes(player) || this.state.clients.includes(player))
			)
			: [];
		const observers = game
			? this.state.clients.filter(client => !game.players.includes(client))
			: [];

		return (
			<div>
				<Container fluid className="Room"><Row>
					<Col xs={0} xl={1} />
					<Col className="GameAreaBorder" xs={12} lg={8} xl={7} ><div className="GameArea">
						<GameHeader game={game} turnState={turnState} />
						{ turnState &&
							<PlayArea gameId={this.props.roomId} game={game} turnState={turnState} myTurn={this.myTurn}
								onAnimationChange={this.handleAnimationChange}
								websocket={this.props.websocket} />
						}
						{ (game && !turnState) && <GameResult game={game} />}
						{ (this.isHost && !turnState) && (<div className="TableBody">
							<center><Button variant="primary" onClick={this.handleStartGame}>
								{game ? "New game" : "Start game"}
							</Button></center>
						</div>) }
						{ !game && <GameRules/> }
					</div></Col>
					<Col className="PlayersAreaBorder" xs={12} lg={4} xl={3} style={{height: "80vh"}}><div className="PlayersArea">
						{ (game && turnState) ? 
							<PlayerList players={game.players} scores={game.scores} activePlayer={game.active_player}
								offlinePlayers={offlinePlayers} observers={observers} /> :
							<GameSetup clients={this.state.clients} bots={this.state.bots} 
								host={this.state.hostName} isHost={this.isHost}
								onAddBot={this.handleAddBot} onRemoveBot={this.handleRemoveBot} />
						}
						<Chat websocket={this.props.websocket} roomId={this.props.roomId} />
					</div></Col>
					<Col xs={0} xl={1} />
				</Row></Container>
			</div>
		);		
	}
}