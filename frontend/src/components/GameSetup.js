export function GameSetup(props) {
	return (
		<div className="GameSetup">
			<div className="Clients">
				<h4>Clients</h4>
				{ props.clients.map(client => (
					<div className="Row" key={client}>
						<div className="Name">{client}</div>
						{ (client === props.host) &&
							<div className="ClientFlags">Host</div>
						}
					</div>
				))}
			</div>
			{ props.bots?.length > 0 && (
				<div className="Bots">
					<h4>Bots</h4>
					{ props.bots.map(bot => (
						<div className="Row" key={bot}>
							<div className="Name">{bot}</div>
							{ props.isHost && (
								<button onClick={props.onRemoveBot} id={bot}>Remove</button>
							)}
						</div>
					))}
				</div>
			)}
			{ props.isHost && (
				<button onClick={props.onAddBot}>Add bot</button>
			)}
			{ props.isHost && (
				<button onClick={props.onStartGame}>Start game</button>
			)}
		</div>
	)
}