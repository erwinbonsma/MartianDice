import { Die } from './Die';

export function DiceRow(props) {
	return (
		<div class="DiceRow">
			{ Object.entries(props.dice).map(([die, number]) =>
				Array(...Array(number)).map(() => (
					<Die face={die}></Die>
				))
			)}
		</div>
	)
}