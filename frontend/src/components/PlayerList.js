import { BotAvatar } from './BotAvatar';
import { PlayerAvatar } from './PlayerAvatar';
import { Separator } from './Separator';

function formatText(text, isActivePlayer, isOffline) {
	return (<div className={isOffline ? "Error" : ""}>
		{ isActivePlayer ? (<b>{text}</b>) : text }
	</div>);
}

export function PlayerList({ players, offlinePlayers, activePlayer, scores, observers, bots }) {
	return (
		<div className="PlayersList">
			<h4 className="TableHeader">Players</h4>
			<div className="TableBody">
			{ players.map(player => {
				const isActivePlayer = player === activePlayer;
				const isOffline = offlinePlayers.includes(player);
				const isBot = !!bots[player];
				return (
					<div key={player} style={{display: "flex"}}>
						<div style={{flex: "1 1", display: "flex", alignItems: "center"}}>
							<div style={{padding: "0 4px 0 0"}}>{ isBot ? <BotAvatar botBehaviour={bots[player]} /> : <PlayerAvatar />}</div>
							<>{formatText(player, isActivePlayer, isOffline)}</>
						</div>
						<div style={{textAlign: "right"}}
							>{formatText(scores[player], isActivePlayer, isOffline)}</div>
					</div>
				)
			})}
			</div>
			<Separator />
			{ observers.length > 0 && (<div className="Observers">
				<h4 className="TableHeader">Observers</h4>
				<div className="TableBody">
				{ observers.map(observer =>
					(<div key={observer} style={{display: "flex", alignItems: "center"}}>
						<div style={{padding: "0 4px 0 0"}}><PlayerAvatar /></div>
						<>{observer}</>
					</div>)
				)}
				</div>
				<Separator />
			</div>)}
		</div>
	)
}