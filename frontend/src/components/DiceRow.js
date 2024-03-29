import { Die } from './Die';
import { useEffect, useState } from 'react';

function createDiceRow(diceDict) {
	const row = Object.entries(diceDict).map(
		([die, number]) => Array.from({length: number}, () => die)
	).flat();

	return row;
}

function updateDiceRow(oldList, targetState) {
	const currentState = oldList.reduce((d, die) => { d[die] = (d[die] || 0) + 1; return d; }, {});
	const newList = Array.from(oldList);
	let updated = false;

	// Remove dies, if needed
	for (let i = 0; i < newList.length; i++) {
		const die = newList[i];
		if (die && (targetState[die] || 0) < currentState[die]) {
			newList[i] = undefined;
			currentState[die] -= 1;
			updated = true;
		}
	}

	// Add dies, if needed. They are always added at the end as in the game there are no rows where
	// dies are both removed and added, so no need to fill gaps in the list.
	for (let die of Object.keys(targetState)) {
		const delta = targetState[die] - (currentState[die] || 0);
		for (let i = 0; i < delta; i++) {
			newList.push(die);
			updated = true;
		}
	}

	// Only return new list when it actually changed to avoid an enless update loop
	return updated ? newList : oldList;
}

export function DiceRow({ dice, padLength, instanceId, onDiceClick }) {
	const [prevInstanceId, setPrevInstanceId] = useState();

	// Maintain array of dice. It is used to keep the dice positions fixed despite dice additions
	// and removals, as long as the prevInstanceId remains the same.
	const [diceRow, setDiceRow] = useState([]);

	useEffect(() => {
		if (instanceId !== prevInstanceId) {
			setDiceRow(createDiceRow(dice));
			setPrevInstanceId(instanceId);
		} else {
			setDiceRow(updateDiceRow(diceRow, dice));
		}
	}, [instanceId, dice, prevInstanceId, diceRow]);

	const numDice = diceRow.length;
	const padDice = padLength ? Math.max(0, padLength - numDice) : 0;
	const counts = { hidden: 0 };

	return (
		<div className="DiceRow">
			{ diceRow.map((d) => {
				const die = d || "hidden";
				const index = counts[die] || 0;
				counts[die] = index + 1;
				return <Die key={`${die}#${index}`} face={die} onClick={onDiceClick}></Die>
			})}
			{ (padDice > 0) && 
				Array.from({length: padDice}, (_, index) => (
					<Die key={`hidden#${index + counts["hidden"]}`} face="hidden"></Die>
				))
			}
		</div>
	)
}