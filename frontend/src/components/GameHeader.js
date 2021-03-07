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
		<Container className="GameHeader">
			<Row>
				<Col as="h4" style={{textAlign:"left"}}>{left}</Col>
				<Col as="h4" sm={6} style={{textAlign: "center"}}>{header}</Col>
				<Col as="h4" style={{textAlign:"right"}}>{right}</Col>
			</Row>
		</Container>
	)
}