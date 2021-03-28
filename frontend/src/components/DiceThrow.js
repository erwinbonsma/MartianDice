import { DiceRow } from './DiceRow';

export function DiceThrow({ diceThrow, instanceId, pad, onDiceClick }) {
	return (
		<div className="DiceThrow">
			<DiceRow dice={diceThrow} instanceId={instanceId} padLength={pad ? 13 : 0}
				onDiceClick={onDiceClick} />
		</div>
	)
}