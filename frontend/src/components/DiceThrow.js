import { DiceRow } from './DiceRow';
import { useEffect, useState } from 'react';

function shuffle(l) {
	for (let i = l.length; --i > 0; ) {
		const j = Math.floor(Math.random() * (i + 1));
		const tmp = l[i];
		l[i] = l[j];
		l[j] = tmp;
	}
}

function shuffleDice(diceDict) {
	const diceList = Object.entries(diceDict).map(
		([die, number]) => Array.from({length: number}, () => die)
	).flat();

	shuffle(diceList);

	return diceList;
}

function addDie(diceDict, die) {
	const newDict = {...diceDict};
	newDict[die] = (newDict[die] || 0) + 1;

	return newDict;
}

export function DiceThrow(props) {
	const {diceThrow, instanceId, pad, onDiceClick, onAnimationDone} = props;

	const [shuffledDice, setShuffledDice] = useState([]);
	const [throwInstanceId, setThrowInstanceId] = useState();
	const [thrownDice, setThrownDice] = useState({});

	useEffect(() => {
		if (instanceId !== throwInstanceId) {
			console.log("Clearing DiceThrow", instanceId, throwInstanceId);
			setThrowInstanceId(instanceId);
			setShuffledDice(shuffleDice(diceThrow));
			setThrownDice({});
		} else if (shuffledDice.length > 0) {
			const throwAnimation = setTimeout(() => {
				setThrownDice(addDie(thrownDice, shuffledDice[0]));
				setShuffledDice(shuffledDice.slice(1));
			}, 1000);

			return function cleanup() {
				clearTimeout(throwAnimation);
			}
		} else {
			setThrownDice(diceThrow)

			if (onAnimationDone) {
				onAnimationDone();
			}
		}
	}, [instanceId, throwInstanceId, shuffledDice, thrownDice, onAnimationDone, diceThrow]);

	return (
		<div className="DiceThrow">
			<DiceRow dice={thrownDice} instanceId={throwInstanceId} padLength={pad ? 13 : 0}
				onDiceClick={onDiceClick} enableLog={true} />
		</div>
	)
}