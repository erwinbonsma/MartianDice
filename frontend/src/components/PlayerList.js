import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

function formatText(text, isActivePlayer, isOffline) {
	return (<div className={isOffline ? "Error" : ""}>
		{ isActivePlayer ? (<b>{text}</b>) : text }
	</div>);
}

export function PlayerList(props) {
	return (
		<Container className="PlayersList">
			<Row className="TableHeader"><Col as="h4">Players</Col></Row>
			{ props.players.map(player => {
				const isActivePlayer = player === props.activePlayer;
				const isOffline = props.offlinePlayers.includes(player);
				return (
					<Row key={player} className="TableRow">
						<Col sm={9}>{formatText(player, isActivePlayer, isOffline)}</Col>
						<Col sm={3} style={{textAlign: "right"}}
							>{formatText(props.scores[player], isActivePlayer, isOffline)}</Col>
					</Row>
				)
			})}
		</Container>
	)
}