export function GameInfo(props) {
	return (
		<div class="GameInfo">
			<h4>Round {props.round} - {props.turn}'s Turn - Throw {props.throw}</h4>
		</div>
	)
}