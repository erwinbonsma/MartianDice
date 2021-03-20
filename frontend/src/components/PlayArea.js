import { AbductionZone } from './AbductionZone';
import { BattleZone } from './BattleZone';
import { PassCheck } from './PassCheck';
import { DiceThrow } from './DiceThrow';
import { TurnResult } from './TurnResult';
import Measure from 'react-measure';
import { useState } from 'react';

export function PlayArea(props) {
	const { turnState } = props;
	const { onThrowAnimationDone } = props; 
	const diceThrow = turnState.throw || {};
	const earthlings = {};
	const combatants = {};

	const [ throwAreaHeight, setThrowAreaHeight ] = useState(0);
	const [ throwAreaWidth, setThrowAreaWidth ] = useState(0);

	Object.entries(turnState.side_dice).forEach(([die, number]) => {
		if (die === "Tank" || die === "Ray") {
			combatants[die] = number;
		} else {
			earthlings[die] = number;
		}
	});

	let handleDiceClick;
	if (props.myTurn && turnState.phase === "PickDice") {
		handleDiceClick = (e) => {
			props.websocket.send(JSON.stringify({
				action: "move",
				game_id: props.gameId,
				pick_die: e.target.id
			}));
		};
	};

	let handlePassAnswer;
	if (props.myTurn && turnState.phase === "CheckPass") {
		handlePassAnswer = (e) => {
			props.websocket.send(JSON.stringify({
				action: "move",
				game_id: props.gameId,
				pass: e.target.id === "yes"
			}));
		}
	}

	const handleDiceThrowResize = (contentRect) => {
		if (contentRect?.bounds) {
			const height = contentRect.bounds.bottom - contentRect.bounds.top;
			const width = contentRect.bounds.right - contentRect.bounds.left;

			if (width !== throwAreaWidth) {
				// When width changes, clear previous maximum height
				setThrowAreaWidth(width);
				setThrowAreaHeight(height);
			} else if (height > throwAreaHeight) {
				// Adapt maximum height
				setThrowAreaHeight(height);
			}
		}
	}

	const turnDone = (turnState.phase === "Done");

	// These instance IDs determine the dice row lifetime. As long as remains the same, dice
	// changes are applied as deltas such that die positions remain fixed.
	const turnInstanceId = `${props.game?.round}-${props.game?.active_player}`;
	const throwInstanceId = `${turnInstanceId}-${turnState.throw_count}`;

	return (
		<div className="PlayArea">
			<div className="GameZoneTopRow">
			{ handlePassAnswer
				? (<div style={{ minHeight: throwAreaHeight }}>
					<PassCheck onAnswer={handlePassAnswer} />
				</div>)
				: ( diceThrow && (
					<Measure bounds onResize={handleDiceThrowResize}>
						{({ measureRef }) => (<div  style={{ minHeight: throwAreaHeight }}>
							<div ref={measureRef}>
								<DiceThrow diceThrow={diceThrow} instanceId={throwInstanceId} pad={!turnDone}
									onAnimationDone={onThrowAnimationDone}
									onDiceClick={handleDiceClick} />
							</div>
							{ turnDone && (
								<TurnResult score={turnState.score} end_cause={turnState.end_cause} />
							)}
						</div>)}
					</Measure>
				))
			}
			</div>
			<BattleZone combatants={combatants} instanceId={turnInstanceId} />
			<AbductionZone earthlings={earthlings} instanceId={turnInstanceId}/>
		</div>
	)
}
