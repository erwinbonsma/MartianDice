import { DiceRow } from './DiceRow';

export function BattleZone(props) {
	return (
		<div className="BattleZone">
			<h4>Battle Zone</h4>
			{ props.combatants.ray && <DiceRow dice={{ray: props.combatants.ray}}></DiceRow> }
			{ props.combatants.tank && <DiceRow dice={{tank: props.combatants.tank}}></DiceRow> }
		</div>		
	)
}