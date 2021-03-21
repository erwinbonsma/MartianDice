import { AbductionZone } from './AbductionZone';
import { BattleZone } from './BattleZone';
import { PassCheck } from './PassCheck';
import { DiceThrow } from './DiceThrow';
import { TurnResult } from './TurnResult';
import Measure from 'react-measure';
import { useEffect, useState } from 'react';
import { applyDieDelta, isDictionaryEmpty } from '../utils';

export function PlayArea(props) {
	const { turnState, websocket, gameId } = props;
	const { onAnimationChange } = props; 
	const targetDiceThrow = turnState.throw;
	const targetSideDice = turnState.side_dice;

	const [ diceThrow, setDiceThrow ] = useState({});
	const [ diceToMove, setDiceToMove ] = useState({});
	const [ combatants, setCombatants ] = useState({});
	const [ earthlings, setEarthlings ] = useState({});
	const [ prevSideDice, setPrevSideDice ] = useState(targetSideDice);
	const [ throwAreaHeight, setThrowAreaHeight ] = useState(0);
	const [ throwAreaWidth, setThrowAreaWidth ] = useState(0);

	// These instance IDs determine the dice row lifetime. As long as remains the same, dice
	// changes are applied as deltas such that die positions remain fixed.
	const turnInstanceId = `${props.game?.round}-${props.game?.active_player}`;
	const throwInstanceId = `${turnInstanceId}-${turnState.throw_count}`;

	// Plan side-dice animation
	useEffect(() => {
		if (isDictionaryEmpty(targetSideDice)) {
			setCombatants({});
			setEarthlings({});
			setPrevSideDice(targetSideDice);
			setDiceToMove({});
		} else {
			let missing = {};
			const prevEarthlings = {};
			const prevCombatants = {};

			for (let die of Object.keys(targetSideDice)) {
				const number = targetSideDice[die] - (prevSideDice[die] || 0);
				if (number > 0) {
					// if (!missing.number) {
					// 	// Only one type of die is moving at anytime
					// 	console.warn("Found multiple die type to move", missing, die);
					// }
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
				const prevDiceThrow = { ...targetDiceThrow };
				prevDiceThrow[missing.die] = missing.number;

				console.log("Initiate move of", missing, prevDiceThrow, prevCombatants, prevEarthlings);

				setDiceThrow(prevDiceThrow);
				setCombatants(prevCombatants);
				setEarthlings(prevEarthlings);
				setDiceToMove(missing);

				onAnimationChange(true);
			}
		}
	}, [targetDiceThrow, prevSideDice, targetSideDice, onAnimationChange]);

	const isAnimating = (prevSideDice !== targetSideDice);
	const handleDiceClick = (e) => {
		websocket.send(JSON.stringify({
			action: "move",
			game_id: gameId,
			pick_die: e.target.id
		}));
	};
	const acceptDiceClick = (!isAnimating && props.myTurn && turnState.phase === "PickDice");

	const handlePassAnswer = (e) => {
		websocket.send(JSON.stringify({
			action: "move",
			game_id: gameId,
			pass: e.target.id === "yes"
		}));
	}
	const acceptPassAnswer = (!isAnimating && props.myTurn && turnState.phase === "CheckPass");

	useEffect(() => {
		if (diceToMove.number) {
			const moveAnimation = setTimeout(() => {
				const die = diceToMove.die;
				setDiceToMove({ die, number: diceToMove.number - 1});

				if (die === "Tank" || die === "Ray") {
					setCombatants( applyDieDelta(combatants, die, 1) );
				} else {
					setEarthlings( applyDieDelta(earthlings, die, 1) );
				}
				setDiceThrow( applyDieDelta(diceThrow, die, -1) );
			}, 1000);

			return function cleanup() {
				clearTimeout(moveAnimation);
			}
		} else {
			if (prevSideDice !== targetSideDice) {
				setPrevSideDice(targetSideDice);
				console.log("Firing animation end from PlayArea");
				onAnimationChange(false);
			}
		}
	}, [diceToMove, diceThrow, combatants, earthlings, prevSideDice, targetSideDice, onAnimationChange]);

	// TODO: Combine height and width into a single dictionary
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

	const handleThrowAnimationChange = (flag) => {
		console.log("handleThrowAnimationChange", flag);
		onAnimationChange(flag || isAnimating);
	}

	const turnDone = (turnState.phase === "Done");

	return (
		<div className="PlayArea">
			<div className="GameZoneTopRow">
			{ acceptPassAnswer
				? (<div style={{ minHeight: throwAreaHeight }}>
					<PassCheck onAnswer={handlePassAnswer} />
				</div>)
				: ( diceThrow && (
					<Measure bounds onResize={handleDiceThrowResize}>
						{({ measureRef }) => (<div  style={{ minHeight: throwAreaHeight }}>
							<div ref={measureRef}>
								<DiceThrow diceThrow={diceThrow} instanceId={throwInstanceId} pad={!turnDone}
									onAnimationChange={handleThrowAnimationChange}
									onDiceClick={acceptDiceClick ? handleDiceClick : undefined} />
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
