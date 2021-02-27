import { DiceRow } from './DiceRow';

export function BattleZone(props) {
	return (
		<div className="BattleZone">
			<h4>Battle Zone</h4>
			{ props.combatants.Ray && <DiceRow dice={{ray: props.combatants.Ray}}></DiceRow> }
			{ props.combatants.Tank && <DiceRow dice={{tank: props.combatants.Tank}}></DiceRow> }
		</div>		
	)
}