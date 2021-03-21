import { DiceRow } from './DiceRow';

export function DiceThrow(props) {
	const { diceThrow, instanceId, pad, onDiceClick } = props;

	return (
		<div className="DiceThrow">
			<DiceRow dice={diceThrow} instanceId={instanceId} padLength={pad ? 13 : 0}
				onDiceClick={onDiceClick} />
		</div>
	)
}