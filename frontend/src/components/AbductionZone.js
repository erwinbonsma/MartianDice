import { DiceRow } from './DiceRow';

export function AbductionZone(props) {
	return (
		<div className="AbductionZone">
			<h4>Abduction Zone</h4>
			<DiceRow dice={props.earthlings} padLength={7}></DiceRow>
		</div>		
	)
}