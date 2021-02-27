export function PlayerList(props) {
	return (
		<div className="PlayerList">
		<h4>Players</h4>
		{ props.players.map(player => (
			<div className="Player" key={player}>
				<div className="PlayerName">{player}</div>
				<div className="PlayerScore">{props.scores[player]}</div>
			</div>
		))}
		</div>
	)
}