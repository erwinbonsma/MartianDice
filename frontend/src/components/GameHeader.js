import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function GameHeader(props) {
	let left, right, header;
	if (props.game) {
		const game = props.game;
		if (game.done) {
			header = "Game completed";
		} else {
			if (props.turnState?.phase === 'PickDice') {
				header = `${game.active_player} to pick a die`;
			} else if (props.turnState?.phase === 'ThrowAgain') {
				header = `${game.active_player} to continue?`;
			} else {
				header = `${game.active_player}'s turn`;
			}
			left = `Round ${game.round}`;
			if (props.turnState?.throw_count > 0) {
				right = `Throw ${props.turnState.throw_count}`;
			}
		}
	} else {
		header = "Waiting for game to start";
	}

	return (
		<div className="GameHeader" style={{display: "flex", padding: "0 1em"}}>
			<h4 style={{textAlign:"left", flex: "1 0"}}>{left}</h4>
			<h4 style={{textAlign: "center", flex: "4 1"}}>{header}</h4>
			<h4 style={{textAlign:"right", flex: "1 0"}}>{right}</h4>
		</div>
	)
}