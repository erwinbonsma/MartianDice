export function GameHeader(props) {
	let header;
	if (props.game) {
		const game = props.game;
		if (game.done) {
			header = "Game completed";
		} else {
			header = `Round ${game.round} - ${game.active_player}'s Turn`;
			if (game.turn_state) {
				header += ` - Throw ${game.turn_state.throw_count}`;
			}
		}
	} else {
		header = "Waiting for game to start";
	}

	return (
		<h4 className="GameHeader">{header}</h4>
	)
}