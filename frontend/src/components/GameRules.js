import { DiceRow } from './DiceRow';
import Accordion from 'react-bootstrap/Accordion'
import Card from 'react-bootstrap/Card'

export function GameRules() {
	return (<Accordion defaultActiveKey="0">
		<Card className="TableBody">
			<Accordion.Toggle as={Card.Header} className="TableHeader" eventKey="0"
				style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
				<DiceRow dice={{tank: 1, ray: 2}}></DiceRow>
				<h4>Rules</h4>
				<DiceRow dice={{human: 1, chicken: 1, cow: 1}}></DiceRow>
			</Accordion.Toggle>
			<Accordion.Collapse eventKey="0">
				<Card.Body><ul style={{padding: "0 0.4em 0 0.4em", fontSize: "smaller"}}>
					<li>Abduct as many earthlings as you can!
						<ul>
						<li>You get a point for each</li>
						<li>You get three bonus points when you collect all three types</li>
						</ul></li>
					<li>Abduction only succeeds when UFOs equal or outnumber tanks
						<ul>
						<li>Due to superior technology your UFOs appear twice as likely</li>
						</ul></li>
					<li>A turn consists of one or more dice throws
						<ul>
						<li>Tanks are automatically set aside</li>
						<li>You then select a die and collect all dice of that type</li>
						<li>You can select each earthling type only once during your turn</li>
						</ul></li>
					<li>Your turn ends when
						<ul>
						<li>You cannot defeat the tanks</li>
						<li>You cannot select a die</li>
						<li>You choose to stop once you can abduct some earthlings</li>
						</ul></li>
					<li>The game ends when a player has 25 points or more</li>
				</ul></Card.Body>
			</Accordion.Collapse>
		</Card>
	</Accordion>)
}