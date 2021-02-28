import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function PlayerList(props) {
	return (
		<Container className="PlayerList">
			<Row><Col as="h4">Players</Col></Row>
			{ props.players.map(player => (
				<Row key={player}>
					<Col sm={9} style={{backgroundColor: "blue"}}>{player}</Col>
					<Col sm={3} style={{textAlign:"right", backgroundColor: "red"}}>{props.scores[player]}</Col>
				</Row>
			))}
		</Container>
	)
}