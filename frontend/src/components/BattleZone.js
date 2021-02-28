import { DiceRow } from './DiceRow';

export function BattleZone(props) {
	const numRays = props.combatants.get("Ray") || 0;
	const numTanks = props.combatants.get("Tank") || 0;
	return (
		<div className="BattleZone">
			<h4>Battle Zone</h4>
			<DiceRow dice={{ray: numRays}} padLength={7}></DiceRow>
			<DiceRow dice={{tank: numTanks}} padLength={7}></DiceRow>
		</div>		
	)
}