export function Die({ face, onClick }) {
	const imageFile = face.toLowerCase() + ".png";
	return (
		<div className="Die">
			<img src={imageFile} alt="{face}" onClick={onClick} id={face}></img>
		</div>
	)
}