export function GameHeader( {game, turnState, slowResponse} ) {
	let left, right, header;
	if (game) {
		if (game.winner) {
			header = "Game completed";
		} else {
			if (turnState?.phase === 'PickDice') {
				header = `${game.active_player} to pick a die`;
			} else if (turnState?.phase === 'CheckPass') {
				header = `${game.active_player} to pass?`;
			} else {
				header = `${game.active_player}'s turn`;
			}
			left = `Round ${game.round}`;
			if (turnState?.throw_count > 0) {
				right = `Throw ${turnState.throw_count}`;
			}
		}
	} else {
		header = "Assembling crew";
	}

	return (
		<div className="GameHeader" style={{display: "flex", padding: "0 1em"}}>
			<h4 style={{textAlign: "left", flex: "2 0"}}>{left}</h4>
			<h4 style={{textAlign: "center", flex: "5 1"}} className={slowResponse ? "Warning" : ""} >{header}</h4>
			<h4 style={{textAlign: "right", flex: "2 0"}}>{right}</h4>
		</div>
	)
}