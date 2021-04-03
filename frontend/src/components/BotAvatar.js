export function BotAvatar({ botBehaviour }) {
	return <img src={`avatar-${botBehaviour}.png`} alt={botBehaviour}
		width={16} height={16}
		style={{margin: "0 2px 0 0"}}/>
}