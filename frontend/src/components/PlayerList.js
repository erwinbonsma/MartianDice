import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

function formatText(text, isActivePlayer) {
	return (<div>
		{ isActivePlayer ? (<b>{text}</b>) : text }
	</div>);
}

export function PlayerList(props) {
	return (
		<Container className="PlayerTable">
			<Row className="TableHeader"><Col as="h4">Players</Col></Row>
			{ props.players.map(player => (
				<Row key={player} className="TableRow">
					<Col sm={9}>{formatText(player, player === props.activePlayer)}</Col>
					<Col sm={3} style={{textAlign: "right"}}
						>{formatText(props.scores[player], player === props.activePlayer)}</Col>
				</Row>
			))}
		</Container>
	)
}