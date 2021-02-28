import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function GameSetup(props) {
	return (
		<div className="GameSetup">
			<h4>Clients</h4>
			<Container className="Clients">
				{ props.clients.map(client => (
					<Row key={client}>
						<Col sm={6}>{client}</Col>
						<Col style={{textAlign: "center"}}>{ (client === props.host) && "Host"}</Col>
					</Row>
				))}
			</Container>
			{ props.bots?.length > 0 && (
				<>
					<h4>Bots</h4>
					<Container className="Bots">
						{ props.bots.map(bot => (
							<Row key={bot}>
								<Col sm={6}>{bot}</Col>
								<Col style={{textAlign: "center"}}>{ props.isHost && (
									<Button className="Button" variant="secondary" size="sm" onClick={props.onRemoveBot} id={bot}>Remove</Button>
								)}</Col>
							</Row>
						))}
					</Container>
				</>
			)}
			{ props.isHost && (
				<Button className="Button" variant="secondary" onClick={props.onAddBot}>Add bot</Button>
			)}
			{ props.isHost && (
				<Button className="Button" variant="primary" onClick={props.onStartGame}>Start game</Button>
			)}
		</div>
	)
}