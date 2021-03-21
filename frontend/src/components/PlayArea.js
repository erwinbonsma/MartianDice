import { AbductionZone } from './AbductionZone';
import { BattleZone } from './BattleZone';
import { PassCheck } from './PassCheck';
import { DiceThrow } from './DiceThrow';
import { TurnResult } from './TurnResult';
import { applyDieDelta, isDictionaryEmpty, shuffle } from '../utils';
import Measure from 'react-measure';
import React from 'react';

function shuffleDice(diceDict) {
	const diceList = Object.entries(diceDict).map(
		([die, number]) => Array.from({length: number}, () => die)
	).flat();

	shuffle(diceList);

	return diceList;
}

export class PlayArea extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			plannedThrowAnimation: undefined,
			diceThrow: {},
			diceToAdd: [],

			plannedMoveAnimation: undefined,
			diceToMove: {},
			combatants: {},
			earthlings: {},
			prevSideDice: {},

			throwArea: { width: 0, height: 0 }
		}

		this.handleDiceClick = this.handleDiceClick.bind(this);
		this.handlePassAnswer = this.handlePassAnswer.bind(this);
		this.handleDiceThrowAreaResize = this.handleDiceThrowAreaResize.bind(this);
	}

	get turnId() {
		return `${this.props.game.round}-${this.props.game.active_player}`;
	}
	get throwId() {
		return `${this.turnInstanceId}-${this.props.turnState.throw_count}`;
	}
	get phaseId() {
		return `${this.throwId}-${this.props.turnState.phase}`;
	}

	get isAnimating() {
		return this.moveAnimation || this.throwAnimation;
	}
	get acceptDiceClick() {
		return (!this.isAnimating && this.props.myTurn && this.props.turnState.phase === "PickDice");
	}
	get acceptPassAnswer() {
		return (!this.isAnimating && this.props.myTurn && this.props.turnState.phase === "CheckPass");
	}
	get targetSideDice() {
		return this.props.turnState.side_dice;
	}

	handleDiceClick(event) {
		this.props.websocket.send(JSON.stringify({
			action: "move",
			game_id: this.props.gameId,
			pick_die: event.target.id
		}));
	}

	handlePassAnswer(event) {
		this.props.websocket.send(JSON.stringify({
			action: "move",
			game_id: this.props.gameId,
			pass: event.target.id === "yes"
		}));
	}

	handleDiceThrowAreaResize(contentRect) {
		if (!contentRect?.bounds) {
			return;
		}
		
		const height = contentRect.bounds.bottom - contentRect.bounds.top;
		const width = contentRect.bounds.right - contentRect.bounds.left;

		if (width !== this.state.throwArea.width) {
			// When width changes, clear previous maximum height
			this.setState({ width, height });
		} else if (height > this.state.throwArea.height) {
			// Adapt maximum height
			this.setState({ height });
		}
	}

	prepareThrowAnimation() {
		const throwId = this.throwId;
		if (this.state.plannedThrowAnimation === throwId) {
			return;
		}

		console.assert(!this.throwAnimation, "Throw animation in progress already");

		const diceThrow = this.props.turnState.throw;
		if (!diceThrow || isDictionaryEmpty(diceThrow)) {
			return;
		}

		this.setState({
			plannedThrowAnimation: throwId,
			startThrowAnimation: true,
			diceToAdd: shuffleDice(diceThrow),
			diceThrow: {}
		});
	}

	startThrowAnimation() {
		if (this.state.startThrowAnimation) {
			console.log("Starting throw animation");
			this.props.onAnimationChange(true);
			this.animateThrow();
			this.setState({
				startThrowAnimation: false
			});
		}
	}

	animateThrow() {
		console.assert(!this.throwAnimation);

		if (this.state.diceToAdd.length > 0) {
			this.throwAnimation = setTimeout(() => {
				this.setState((state) => ({
					diceThrow: applyDieDelta(this.state.diceThrow, this.state.diceToAdd[0], 1),
					diceToAdd: this.state.diceToAdd.slice(1)
				}));

				this.throwAnimation = undefined;
				this.animateThrow();
			}, 500);
		} else {
			console.log("Signal throw animation end");
			this.props.onAnimationChange(false);
		}
	}

	prepareMoveAnimation() {
		const phaseId = this.phaseId;
		if (this.state.plannedMoveAnimation === phaseId) {
			return;
		}

		if (isDictionaryEmpty(this.targetSideDice)) {
			this.setState({
				combatants: {},
				earthlings: {},
				prevSideDice: {},
				diceToMove: {},
				plannedMoveAnimation: phaseId
			});

			return;
		}
		
		let missing = {};
		const prevEarthlings = {};
		const prevCombatants = {};
		const targetSideDice = this.targetSideDice;
		const prevSideDice = this.state.prevSideDice;

		for (let die of Object.keys(targetSideDice)) {
			const number = targetSideDice[die] - (prevSideDice[die] || 0);

			if (number > 0) {
				console.assert(!missing.number, "Found multiple die type to move");
				missing = { die, number };
				if (prevSideDice[die]) {
					prevCombatants[die] = prevSideDice[die];
				}
			} else {
				if (die === "Tank" || die === "Ray") {
					prevCombatants[die] = targetSideDice[die];
				} else {
					prevEarthlings[die] = targetSideDice[die];
				}	
			}
		}

		if (missing.number) {
			const prevDiceThrow = { ...this.props.turnState.throw };
			prevDiceThrow[missing.die] = missing.number;

			console.log("Initiate move of", missing, prevDiceThrow, prevCombatants, prevEarthlings);

			this.setState({
				diceThrow: prevDiceThrow,
				combatants: prevCombatants,
				earthlings: prevEarthlings,
				diceToMove: missing,
				plannedMoveAnimation: phaseId,
				startMoveAnimation: true
			});
		} else {
			// No move animation required
			this.setState({
				plannedMoveAnimation: phaseId
			});
		}
	}

	startMoveAnimation() {
		if (this.state.startMoveAnimation) {
			console.log("Starting move animation");
			this.props.onAnimationChange(true);
			this.animateDiceMoves();
			this.setState({
				startMoveAnimation: false
			});
		}
	}

	animateDiceMoves() {
		console.assert(!this.moveAnimation);

		if (this.state.diceToMove.number) {
			this.moveAnimation = setTimeout(() => {
				const die = this.state.diceToMove.die;

				this.setState((state) => ({
					diceThrow: applyDieDelta(state.diceThrow, die, -1),
					diceToMove: { die, number: state.diceToMove.number - 1}
				}));

				if (die === "Tank" || die === "Ray") {
					this.setState((state) => ({
						combatants: applyDieDelta(state.combatants, die, 1)
					}));
				} else {
					this.setState((state) => ({
						earthlings: applyDieDelta(state.earthlings, die, 1)
					}));
				}

				this.moveAnimation = undefined;
				this.animateDiceMoves();
			}, 1000);
		} else {
			this.props.onAnimationChange(false);
			this.setState({
				prevSideDice: this.targetSideDice
			});
		}
	}

	componentWillUnmount() {
		if (this.moveAnimation) {
			clearTimeout(this.moveAnimation);
			this.moveAnimation = undefined;
		}

		if (this.throwAnimation) {
			clearTimeout(this.throwAnimation);
			this.throwAnimation = undefined;
		}
	}

	componentDidUpdate() {
		this.prepareThrowAnimation();
		this.startThrowAnimation();

		this.prepareMoveAnimation();
		this.startMoveAnimation();
	}

	render() {
		const turnState = this.props.turnState;
		const turnDone = (turnState.phase === "Done");

		return (
			<div className="PlayArea">
				<div className="GameZoneTopRow">
				{ this.acceptPassAnswer
					? (<div style={{ minHeight: this.state.throwArea.height }}>
						<PassCheck onAnswer={this.handlePassAnswer} />
					</div>)
					: ( this.state.diceThrow && (
						<Measure bounds onResize={this.handleDiceThrowAreaResize}>
							{({ measureRef }) => (<div style={{ minHeight: this.state.throwArea.height }}>
								<div ref={measureRef}>
									<DiceThrow diceThrow={this.state.diceThrow} pad={!turnDone}
										instanceId={this.throwId}
										onAnimationChange={this.handleThrowAnimationChange}
										onDiceClick={this.acceptDiceClick ? this.handleDiceClick : undefined} />
								</div>
								{ turnDone && (
									<TurnResult score={turnState.score} end_cause={turnState.end_cause} />
								)}
							</div>)}
						</Measure>
					))
				}
				</div>
				<BattleZone combatants={this.state.combatants} instanceId={this.turnId} />
				<AbductionZone earthlings={this.state.earthlings} instanceId={this.turnId} />
			</div>
		)	
	}
}
