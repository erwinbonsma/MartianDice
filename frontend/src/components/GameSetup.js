import { Separator } from './Separator';
import Button from 'react-bootstrap/Button';
import DropdownButton from 'react-bootstrap/DropdownButton';
import Dropdown from 'react-bootstrap/Dropdown';

export function GameSetup(props) {
	return (
		<div className="GameSetup">
			<div className="ClientTable">
				<h4 className="TableHeader">Humans</h4>
				<div className="TableBody">
				{ props.clients.map(client => (
					<div key={client} style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
						<div >{client}</div>
						<div style={{textAlign: "right"}}>{ (client === props.host) && "Host"}</div>
					</div>
				))}
				</div>
				<Separator />
			</div>
			{ (props.bots?.length > 0 || props.isHost) && (
				<div className="BotsTable">
					<h4 className="TableHeader">Bots</h4>
					<div className="TableBody">
					{ props.bots.map(bot => (
						<div key={bot} style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
							<div>{bot}</div>
							<div style={{textAlign: "right"}}>{ props.isHost && (
								<Button className="Button" variant="secondary" size="sm" onClick={props.onRemoveBot} id={bot}>Remove</Button>
							)}</div>
						</div>
					))}
					{ props.isHost && (
						<div>
							<DropdownButton variant="secondary" title="Add bot" onSelect={props.onAddBot} style={{margin: "0.3em 0 0.5em"}}>
								<Dropdown.Item eventKey="random">Random</Dropdown.Item>
								<Dropdown.Item eventKey="aggressive">Aggressive</Dropdown.Item>
								<Dropdown.Item eventKey="defensive">Defensive</Dropdown.Item>
								<Dropdown.Item eventKey="smart">Smart</Dropdown.Item>
							</DropdownButton>
						</div>
					)}
					</div>
					<Separator />
				</div>
			)}
		</div>
	)
}