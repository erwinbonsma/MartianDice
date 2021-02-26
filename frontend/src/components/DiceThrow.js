import { DiceRow } from './DiceRow';

export function DiceThrow(props) {
	return (
		<div class="DiceThrow">
			<DiceRow dice={props.throw}></DiceRow>
		</div>
	)
}