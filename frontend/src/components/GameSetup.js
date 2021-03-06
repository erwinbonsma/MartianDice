import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function GameSetup(props) {
	return (
		<div className="GameSetup">
			<div className="ClientTable">
				<h4 className="TableHeader">Humans</h4>
				<Container>
				{ props.clients.map(client => (
					<Row key={client} className="TableRow">
						<Col sm={6}>{client}</Col>
						<Col style={{textAlign: "center"}}>{ (client === props.host) && "Host"}</Col>
					</Row>
				))}
				</Container>
			</div>
			{ props.bots?.length > 0 && (
				<div className="BotsTable">
					<h4 className="TableHeader">Bots</h4>
					<Container>
					{ props.bots.map(bot => (
						<Row key={bot} className="TableRow">
							<Col sm={6}>{bot}</Col>
							<Col style={{textAlign: "center"}}>{ props.isHost && (
								<Button className="Button" variant="secondary" size="sm" onClick={props.onRemoveBot} id={bot}>Remove</Button>
							)}</Col>
						</Row>
					))}
					</Container>
				</div>
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