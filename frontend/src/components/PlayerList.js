import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function PlayerList(props) {
	return (
		<Container className="PlayerTable">
			<Row className="TableHeader"><Col as="h4">Players</Col></Row>
			{ props.players.map(player => (
				<Row key={player} className="TableRow">
					<Col sm={9}>{player}</Col>
					<Col sm={3} style={{textAlign: "right"}}>{props.scores[player]}</Col>
				</Row>
			))}
		</Container>
	)
}