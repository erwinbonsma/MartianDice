import { AbductionZone } from './AbductionZone';
import { BattleZone } from './BattleZone';
import { ContinueTurnCheck } from './ContinueTurnCheck';
import { DiceThrow } from './DiceThrow';
import { TurnResult } from './TurnResult';

export function PlayArea(props) {
	const game = props.game;
	const diceThrow = game.turn_state.throw || {};
	const earthlings = {};
	const combatants = {};

	Object.entries(game.turn_state.side_dice).forEach(([die, number]) => {
		if (die === "Tank" || die === "Ray") {
			combatants[die] = number;
		} else {
			earthlings[die] = number;
		}
	});

	let onDiceClick;
	if (props.my_turn && game.turn_state.phase === "PickDice") {
		onDiceClick = (e) => {
			props.websocket.send(JSON.stringify({
				action: "move",
				"pick-die": e.target.id
			}));
		};
	};

	let onCheckContinue;
	if (props.my_turn && game.turn_state.phase === "CheckEndTurn") {
		onCheckContinue = (e) => {
			props.websocket.send(JSON.stringify({
				action: "move",
				"throw-again": e.target.id === "yes"
			}));
		}
	}

	let turnResult;
	if (game.turn_state.phase === "Done") {
		turnResult = (
			<TurnResult score={game.turn_state.score} end_cause={game.turn_state.end_cause}></TurnResult>
		);
	}

	return (
		<div>
			<div className="GameZoneTopRow">
			{ onCheckContinue
				? <ContinueTurnCheck onAnswer={onCheckContinue}></ContinueTurnCheck>
				: turnResult
					? turnResult 
					: <DiceThrow throw={diceThrow} onDiceClick={onDiceClick}></DiceThrow>
			}
			</div>
			<BattleZone combatants={combatants}></BattleZone>
			<AbductionZone earthlings={earthlings}></AbductionZone>
		</div>
	)
}
