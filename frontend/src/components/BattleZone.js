import { DiceRow } from './DiceRow';

export function BattleZone(props) {
	const numRays = props.combatants["Ray"] || 0;
	const numTanks = props.combatants["Tank"] || 0;
	return (
		<div className="BattleZone">
			<h4>Battle Zone</h4>
			<DiceRow dice={{ray: numRays}} padLength={7} instanceId={props.instanceId} />
			<DiceRow dice={{tank: numTanks}} padLength={7} instanceId={props.instanceId} />
		</div>		
	)
}