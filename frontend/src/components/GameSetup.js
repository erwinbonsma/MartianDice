import { Separator } from './Separator';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function GameSetup(props) {
	return (
		<div className="GameSetup">
			<div className="ClientTable">
				<h4 className="TableHeader">Humans</h4>
				<Container className="TableBody">
				{ props.clients.map(client => (
					<Row key={client}>
						<Col sm={6}>{client}</Col>
						<Col style={{textAlign: "right"}}>{ (client === props.host) && "Host"}</Col>
					</Row>
				))}
				</Container>
				<Separator />
			</div>
			{ (props.bots?.length > 0 || props.isHost) && (
				<div className="BotsTable">
					<h4 className="TableHeader">Bots</h4>
					<Container className="TableBody">
					{ props.bots.map(bot => (
						<Row key={bot}>
							<Col sm={6}>{bot}</Col>
							<Col style={{textAlign: "right"}}>{ props.isHost && (
								<Button className="Button" variant="secondary" size="sm" onClick={props.onRemoveBot} id={bot}>Remove</Button>
							)}</Col>
						</Row>
					))}
					{ props.isHost && (
						<Row>
							<Col><Button variant="secondary" onClick={props.onAddBot}
								style={{margin: "0 0 0.5em"}}>Add bot</Button></Col>
						</Row>
					)}
					</Container>
					<Separator />
				</div>
			)}
		</div>
	)
}