import { DiceRow } from './DiceRow';

export function AbductionZone({ earthlings, instanceId }) {
	return (
		<div className="AbductionZone">
			<h4>Abduction Zone</h4>
			<DiceRow dice={earthlings} padLength={7} instanceId={instanceId} />
		</div>		
	)
}