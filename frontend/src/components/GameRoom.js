import { Chat } from './Chat';
import { GameHeader } from './GameHeader';
import { GameResult } from './GameResult';
import { GameRules } from './GameRules';
import { GameSetup } from './GameSetup';
import { PlayArea } from './PlayArea';
import { PlayerList } from './PlayerList';
import config from '../utils/config';
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
			bots: {},
			nextBotId: 1,
			transitionTurns: [],
			isAnimating: false,
			lastUpdate: Date.now(),
			slowUpdate: false
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
	get myMove() {
		return !this.isReplaying && (this.props.playerName === this.state.futureGame?.active_player);
	}
	get botMove() {
		return !this.isReplaying && this.state.bots[this.state.futureGame?.active_player];
	}
	get turnState() {
		return this.state.transitionTurns.length > 0
			? this.state.transitionTurns[0]
			: this.state.futureGame?.turn_state;
	}

	handleAddBot(botBehaviour) {
		this.setState((state) => {
			const botName = `Bot-${state.nextBotId}`;
			return {
				bots: { ...state.bots, [botName]: botBehaviour},
				nextBotId: state.nextBotId + 1
			}
		});
	}

	handleRemoveBot(event) {
		const botName = event.target.id;
		this.setState((state) => {
			const { [botName]: _, ...bots } = state.bots;
			return { bots };
		});
	}

	handleStartGame() {
		this.props.websocket.send(JSON.stringify({
			action: "start-game",
			room_id: this.props.roomId,
			game_config: {
				bots: this.state.bots
			}
		}));
	}

	handleAnimationChange(flag) {
		if (flag !== this.state.isAnimating) {
			if (flag) {
				clearTimeout(this.turnAnimation);
				this.turnAnimation = undefined;
			}

			this.setState({
				isAnimating: flag
			});	
		}
	}

	handleMessage(event) {
		const msg = JSON.parse(event.data);
		console.log("Message:", msg);
		switch (msg.type) {
			case "clients":
				this.setState({
					hostName: msg.host,
					clients: msg.clients
				});
				break;
			case "game-config":
				this.setState((state, props) => {
					if (this.props.playerName !== this.state.hostName) {
						return {
							bots: msg.game_config.bots,
							nextBotId: msg.game_config.next_bot_id
						}
					}
				});
				break;
			case "game-state":
				this.clearWatchdog();
				this.setState((state) => {
					if (state.game && state.game.id !== msg.state.prev_id) {
						console.warn(`Unexpected state transition: ${state.game.id} != ${msg.state.prev_id}`);
					}
					return {
						transitionTurns: msg.turn_state_transitions,
						futureGame: msg.state,
						// Ensure game state is always set when there is a turn state
						game: state.game || msg.state,
						slowUpdate: false
					}
				});
				break;
			case "response":
				if (msg.status === "error") {
					console.error(msg.details);
				} else {
					console.info(msg.details);
				}
				break;
			default:
				// May be handled elsewhere
		}
	}

	animateTransitions() {
		if (
			this.turnAnimation ||
			this.state.transitionTurns.length === 0 ||
			this.state.isAnimating
		) {
			return;
		}

		let transitionDelay = config.TRANSITION_DELAY; // Default

		if (
			this.state.transitionTurns.length === 1 &&
			this.state.futureGame.turn_state?.phase === "PickDice"
		) {
			// Do not make player wait unnecessarily before picking a die
			transitionDelay = config.FAST_TRANSITION_DELAY;
		} else if (this.state.transitionTurns[0].phase === "Done") {
			// Show turn result for a bit longer 
			transitionDelay = config.SLOW_TRANSITION_DELAY;
		}

		this.turnAnimation = setTimeout(() => {
			this.turnAnimation = undefined;

			// Finished animating current transition. Move to the next
			this.setState((state) => {
				return {
					transitionTurns: state.transitionTurns.slice(1),
					lastUpdate: Date.now()
				};
			});
		}, transitionDelay);
	}

	triggerBotMove() {
		if (this.botMoveTrigger) {
			// Event trigger already scheduled
			return;
		}

		if (!this.isHost || !this.botMove) {
			// Bot move does not require triggering (yet)
			return;
		}
		
		this.botMoveTrigger = setTimeout(() => {
			this.botMoveTrigger = undefined;
			const activePlayer = this.state.game.active_player;
			const behaviour = this.state.bots[activePlayer];

			this.props.websocket.send(JSON.stringify({
				action: "bot-move",
				game_id: this.props.roomId,
				game_state: this.state.game,
				bot_behaviour: behaviour
			}));
		}, 2000);
	}

	setWatchdog() {
		if (this.watchdog || this.isReplaying || this.state.slowUpdate) {
			return;
		}

		this.watchdog = setTimeout(() => {
			console.log("Watchdog expired");
			this.watchdog = undefined;

			if (this.botMove) {
				console.warn("Bot is not responding - host problem?");
				this.props.websocket.send(JSON.stringify({
					action: "switch-host",
					room_id: this.props.roomId
				}));
			} else {
				// Player is not responding. Enable end-turn button
				this.setState({
					slowUpdate: true
				});
			}
		}, config.MAX_MOVE_TIME_IN_SECONDS * 1000);
	}

	clearWatchdog() {
		if (this.watchdog) {
			clearTimeout(this.watchdog);
			this.watchdog = undefined;
		}
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

	sendConfigUpdate() {
		this.props.websocket.send(JSON.stringify({
			action: "update-config",
			room_id: this.props.roomId,
			game_config: {
				bots: this.state.bots,
				next_bot_id: this.state.nextBotId
			}
		}));
	}

	welcomeNewClients(prevClients) {
		const newClients = new Set(this.state.clients);
		prevClients.forEach(oldClient => { newClients.delete(oldClient); });
		newClients.delete(this.props.playerName);

		if (newClients.size > 0) {
			const optGameConfig = this.state.futureGame ? {
				game_state: this.state.futureGame
			} : {};

			this.props.websocket.send(JSON.stringify({
				action: "send-welcome",
				room_id: this.props.roomId,
				to_clients: [...newClients],
				game_config: {
					bots: this.state.bots,
					next_bot_id: this.state.nextBotId
				},
				...optGameConfig
			}));
		}
	}

	componentDidMount() {
		this.props.websocket.addEventListener('message', this.handleMessage);

		this.props.websocket.send(JSON.stringify({
			action: "send-clients",
			room_id: this.props.roomId
		}));
	}
  
	componentWillUnmount() {
		this.props.websocket.removeEventListener('message', this.handleMessage);

		if (this.turnAnimation) {
			clearTimeout(this.turnAnimation);
			this.turnAnimation = undefined;
		}

		if (this.botMoveTrigger) {
			clearTimeout(this.botMoveTrigger);
			this.botMoveTrigger = undefined;
		}

		this.clearWatchdog();
	}

	componentDidUpdate(prevProps, prevState) {
		this.animateTransitions();
		this.triggerBotMove();
		this.updateGame();
		this.setWatchdog();

		if (this.isHost) {
			if (prevState.bots !== this.state.bots) {
				this.sendConfigUpdate();
			}
			if (prevState.clients !== this.state.clients) {
				this.welcomeNewClients(prevState.clients);
			}
		}
	}

	render() {
		const game = this.state.game;
		const turnState = this.turnState;

		console.log("turnState =", turnState);
		console.log("game =", game);

		const offlinePlayers = game
			? game.players.filter(
				player => !(this.state.bots[player] || this.state.clients.includes(player))
			)
			: [];
		const observers = game
			? this.state.clients.filter(client => !game.players.includes(client))
			: [];

		return (
			<div>
				<Container className="Room"><Row>
					<Col className="GameAreaBorder" xs={12} lg={8} ><div className="GameArea">
						<GameHeader game={game} turnState={turnState} slowResponse={this.state.slowUpdate} />
						{ turnState &&
							<PlayArea gameId={this.props.roomId} instanceId={this.props.instanceId}
								game={game} turnState={turnState} myTurn={this.myMove}
								onAnimationChange={this.handleAnimationChange}
								audioTracks={this.props.audioTracks} enableSound={this.props.enableSound}
								websocket={this.props.websocket} slowResponse={this.state.slowUpdate} />
						}
						{ (game && !turnState) && <GameResult game={game} />}
						{ (this.isHost && !turnState) && (<div className="TableBody">
							<center><Button variant="primary" onClick={this.handleStartGame}>
								{game ? "New game" : "Start game"}
							</Button></center>
						</div>) }
						{ !game && <GameRules/> }
					</div></Col>
					<Col className="PlayersAreaBorder" xs={12} lg={4} style={{height: "80vh"}}><div className="PlayersArea">
						{ (game && turnState) ? 
							<PlayerList players={game.players} scores={game.scores} activePlayer={game.active_player}
								offlinePlayers={offlinePlayers} observers={observers} /> :
							<GameSetup clients={this.state.clients} bots={this.state.bots} 
								host={this.state.hostName} isHost={this.isHost}
								onAddBot={this.handleAddBot} onRemoveBot={this.handleRemoveBot} />
						}
						<Chat websocket={this.props.websocket} roomId={this.props.roomId} />
					</div></Col>
				</Row></Container>
			</div>
		);		
	}
}