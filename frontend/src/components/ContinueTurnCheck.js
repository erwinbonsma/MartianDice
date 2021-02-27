export function ContinueTurnCheck(props) {
	return (
		<div className="Row">
			Continue turn?
			<button id="yes" onClick={props.onAnswer}>Yes</button>
			<button id="no" onClick={props.onAnswer}>No</button>
		</div>
	)
}