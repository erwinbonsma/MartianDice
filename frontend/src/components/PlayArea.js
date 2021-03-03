import { AbductionZone } from './AbductionZone';
import { BattleZone } from './BattleZone';
import { ContinueTurnCheck } from './ContinueTurnCheck';
import { DiceThrow } from './DiceThrow';
import { TurnResult } from './TurnResult';
import Measure from 'react-measure';
import { useState } from 'react';

export function PlayArea(props) {
	const turnState = props.turnState;
	const diceThrow = turnState.throw || {};
	const earthlings = {};
	const combatants = {};

	const [ throwAreaHeight, setThrowAreaHeight ] = useState(0);

	Object.entries(turnState.side_dice).forEach(([die, number]) => {
		if (die === "Tank" || die === "Ray") {
			combatants[die] = number;
		} else {
			earthlings[die] = number;
		}
	});

	let onDiceClick;
	if (props.myTurn && turnState.phase === "PickDice") {
		onDiceClick = (e) => {
			props.websocket.send(JSON.stringify({
				action: "move",
				game_id: props.gameId,
				pick_die: e.target.id
			}));
		};
	};

	let onCheckContinue;
	if (props.myTurn && turnState.phase === "ThrowAgain") {
		onCheckContinue = (e) => {
			props.websocket.send(JSON.stringify({
				action: "move",
				game_id: props.gameId,
				throw_again: e.target.id === "yes"
			}));
		}
	}

	const onDiceThrowResize = (contentRect) => {
		if (contentRect?.bounds) {
			const height = contentRect.bounds.bottom - contentRect.bounds.top;
			if (height > throwAreaHeight) {
				setThrowAreaHeight(height);
			}
		}
	}

	return (
		<div>
			<div className="GameZoneTopRow">
			{ onCheckContinue
				? (<div style={{ minHeight: throwAreaHeight }}>
					<ContinueTurnCheck onAnswer={onCheckContinue}></ContinueTurnCheck>
				</div>)
				: (turnState.phase === "Done")
					? (<div style={{ minHeight: throwAreaHeight }}>
						<TurnResult score={turnState.score} end_cause={turnState.end_cause}></TurnResult>
					</div>)
					: (<Measure bounds onResize={onDiceThrowResize}>
						{({ measureRef }) => (
						  <div ref={measureRef}>
							<DiceThrow throw={diceThrow} onDiceClick={onDiceClick}></DiceThrow>
						  </div>
					)}</Measure>)
			}
			</div>
			<BattleZone combatants={combatants}></BattleZone>
			<AbductionZone earthlings={earthlings}></AbductionZone>
		</div>
	)
}
