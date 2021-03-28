import { DiceRow } from './DiceRow';

export function BattleZone({ combatants, instanceId }) {
	const numRays = combatants["Ray"] || 0;
	const numTanks = combatants["Tank"] || 0;

	return (
		<div className="BattleZone">
			<h4>Battle Zone</h4>
			<DiceRow dice={{ray: numRays}} padLength={7} instanceId={instanceId} />
			<DiceRow dice={{tank: numTanks}} padLength={7} instanceId={instanceId} />
		</div>		
	)
}