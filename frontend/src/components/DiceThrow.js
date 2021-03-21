import { DiceRow } from './DiceRow';
import { useEffect, useState } from 'react';
import { applyDieDelta, isDictionaryEmpty, shuffle } from '../utils';

function shuffleDice(diceDict) {
	const diceList = Object.entries(diceDict).map(
		([die, number]) => Array.from({length: number}, () => die)
	).flat();

	shuffle(diceList);

	return diceList;
}

export function DiceThrow(props) {
	const {diceThrow, instanceId, pad, onDiceClick, onAnimationChange} = props;

	const [shuffledDice, setShuffledDice] = useState([]);
	const [throwInstanceId, setThrowInstanceId] = useState();
	const [thrownDice, setThrownDice] = useState({});

	useEffect(() => {
		if (instanceId !== throwInstanceId) {
			console.log("Clearing DiceThrow", instanceId, throwInstanceId);
			setThrowInstanceId(instanceId);
			setShuffledDice(shuffleDice(diceThrow));
			setThrownDice({});

			if (!isDictionaryEmpty(diceThrow)) {
				onAnimationChange(true);
			}
		}
	}, [instanceId, throwInstanceId, diceThrow, onAnimationChange]);
	
	useEffect(() => {
		if (shuffledDice.length > 0) {
			const throwAnimation = setTimeout(() => {
				setThrownDice(applyDieDelta(thrownDice, shuffledDice[0], 1));
				setShuffledDice(shuffledDice.slice(1));
			}, 500);

			return function cleanup() {
				clearTimeout(throwAnimation);
			}
		} else {
			if (thrownDice !== diceThrow) {
				setThrownDice(diceThrow);
				onAnimationChange(false);
			}
		}
	}, [shuffledDice, thrownDice, onAnimationChange, diceThrow]);

	return (
		<div className="DiceThrow">
			<DiceRow dice={thrownDice} instanceId={throwInstanceId} padLength={pad ? 13 : 0}
				onDiceClick={onDiceClick} enableLog={true} />
		</div>
	)
}