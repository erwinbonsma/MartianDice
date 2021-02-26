export function PlayerList(props) {
	return (
		<div class="PlayerList">
		<h4>Players</h4>
		{ props.players.map(player => (
			<div class="Player">
				<div class="PlayerName">{player}</div>
				<div class="PlayerScore">{props.scores[player]}</div>
			</div>
		))}
		</div>
	)
}