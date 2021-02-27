import { DiceRow } from './DiceRow';

export function BattleZone(props) {
	return (
		<div className="BattleZone">
			<h4>Battle Zone</h4>
			{ props.combatants.has("Ray") && <DiceRow dice={{ray: props.combatants.get("Ray")}}></DiceRow> }
			{ props.combatants.has("Tank") && <DiceRow dice={{tank: props.combatants.get("Tank")}}></DiceRow> }
		</div>		
	)
}