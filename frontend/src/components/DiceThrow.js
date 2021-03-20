import { DiceRow } from './DiceRow';

export function DiceThrow(props) {
	return (
		<div className="DiceThrow">
			<DiceRow dice={props.throw} instanceId={props.instanceId}
				onDiceClick={props.onDiceClick} padLength={props.pad ? 13 : 0} />
		</div>
	)
}