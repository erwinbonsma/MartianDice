export function Die(props) {
	const imageFile = props.face + ".png";
	return (
		<div className="Die">
			<img src={imageFile} width="75" height="75" alt="{props.face"></img>
		</div>
	)
}