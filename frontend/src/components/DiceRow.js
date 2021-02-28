import { Die } from './Die';

export function DiceRow(props) {
	const numDice = Object.entries(props.dice).reduce((sum, [_, number]) => sum + number, 0);
	const padDice = props.padLength ? Math.max(0, props.padLength - numDice) : 0;

	return (
		<div className="DiceRow">
			{ Object.entries(props.dice).map(([die, number]) =>
				Array.from({length: number}, (_, index) => (
					<Die key={`${die}#${index}`} face={die} onClick={props.onDiceClick}></Die>
				))
			)}
			{ (padDice > 0) && 
				Array.from({length: padDice}, (_, index) => (
					<Die key={`hidden#${index}`} face="hidden"></Die>
				))
			}
		</div>
	)
}