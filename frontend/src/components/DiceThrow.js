import { DiceRow } from './DiceRow';

export function DiceThrow(props) {
	return (
		<div className="DiceThrow">
			<DiceRow dice={props.throw} onDiceClick={props.onDiceClick}></DiceRow>
		</div>
	)
}