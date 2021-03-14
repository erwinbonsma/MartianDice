import { Separator } from './Separator';

function formatText(text, isActivePlayer, isOffline) {
	return (<div className={isOffline ? "Error" : ""}>
		{ isActivePlayer ? (<b>{text}</b>) : text }
	</div>);
}

export function PlayerList(props) {
	return (
		<div className="PlayersList">
			<h4 className="TableHeader">Players</h4>
			<div className="TableBody">
			{ props.players.map(player => {
				const isActivePlayer = player === props.activePlayer;
				const isOffline = props.offlinePlayers.includes(player);
				return (
					<div key={player} style={{display: "flex"}}>
						<div style={{flex: "1 1"}}
							>{formatText(player, isActivePlayer, isOffline)}</div>
						<div style={{textAlign: "right"}}
							>{formatText(props.scores[player], isActivePlayer, isOffline)}</div>
					</div>
				)
			})}
			</div>
			<Separator />
			{ props.observers.length > 0 && (<div className="Observers">
				<h4 className="TableHeader">Observers</h4>
				<div className="TableBody">
				{ props.observers.map(observer =>
					(<div key={observer}>{observer}</div>)
				)}
				</div>
				<Separator />
			</div>)}
		</div>
	)
}