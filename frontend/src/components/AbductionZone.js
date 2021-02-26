import { DiceRow } from './DiceRow';

export function AbductionZone(props) {
	return (
		<div class="AbductionZone">
			<h4>Abduction Zone</h4>
			{ Object.entries(props.earthlings).map(([earthling, number]) => (
				<DiceRow key={earthling} dice={{[earthling]: number}}></DiceRow>
			))}
		</div>		
	)
}