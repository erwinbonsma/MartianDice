import { DiceRow } from './DiceRow';

export function AbductionZone(props) {
	return (
		<div className="AbductionZone">
			<h4>Abduction Zone</h4>
			{ Array.from(props.earthlings).map(([earthling, number]) => (
				<DiceRow key={earthling} dice={{[earthling]: number}}></DiceRow>
			))}
		</div>		
	)
}