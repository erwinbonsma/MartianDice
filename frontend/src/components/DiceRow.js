import { Die } from './Die';

export function DiceRow(props) {
	return (
		<div className="DiceRow">
			{ Object.entries(props.dice).map(([die, number]) =>
				Array.from({length: number}, (_, index) => (
					<Die key={`${die}#${index}`} face={die}></Die>
				))
			)}
		</div>
	)
}