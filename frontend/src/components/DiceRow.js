import { Die } from './Die';

export function DiceRow(props) {
	return (
		<div class="diceRow">
			{ props.dice.map((die) => (
				<Die face={die}></Die>
			))}
		</div>
	)
}