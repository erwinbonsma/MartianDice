export function Die(props) {
	const imageFile = props.face.toLowerCase() + ".png";
	return (
		<div className="Die">
			<img src={imageFile} alt="{props.face}" onClick={props.onClick} id={props.face}></img>
		</div>
	)
}