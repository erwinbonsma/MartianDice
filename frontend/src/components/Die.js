export function Die(props) {
	const imageFile = props.face + ".png";
	return (
		<div class="die">
			<img src={imageFile} width="75" height="75" alt="{props.face"></img>
		</div>
	)
}