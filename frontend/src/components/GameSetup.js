import { isDictionaryEmpty } from '../utils';
import { BotAvatar } from './BotAvatar';
import { PlayerAvatar } from './PlayerAvatar';
import { Separator } from './Separator';
import Button from 'react-bootstrap/Button';
import DropdownButton from 'react-bootstrap/DropdownButton';
import Dropdown from 'react-bootstrap/Dropdown';

export function GameSetup({ clients, bots, host, isHost, onAddBot, onRemoveBot }) {
	return (
		<div className="GameSetup">
			<div className="ClientTable">
				<h4 className="TableHeader">Humans</h4>
				<div className="TableBody">
				{ clients.map(client => (
					<div key={client} style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
						<div><PlayerAvatar />{client}</div>
						<div style={{textAlign: "right"}}>{ (client === host) && "Host"}</div>
					</div>
				))}
				</div>
				<Separator />
			</div>
			{ (!isDictionaryEmpty(bots) || isHost) && (
				<div className="BotsTable">
					<h4 className="TableHeader">Bots</h4>
					<div className="TableBody">
					{ Object.entries(bots).map(([name, behaviour]) => (
						<div key={name} style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
							<div><BotAvatar botBehaviour={behaviour} />{name}</div>
							<div style={{textAlign: "right"}}>{ isHost && (
								<Button className="Button" variant="secondary" size="sm" onClick={onRemoveBot} id={name}>Remove</Button>
							)}</div>
						</div>
					))}
					{ isHost && (
						<div>
							<DropdownButton variant="secondary" title="Add bot" onSelect={onAddBot} style={{margin: "0.3em 0 0.5em"}}>
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