import Button from 'react-bootstrap/Button';

export function ContinueTurnCheck(props) {
	return (
		<div className="Row">
			Continue turn?
			<Button id="yes" onClick={props.onAnswer}>Yes</Button>
			<Button id="no" onClick={props.onAnswer}>No</Button>
		</div>
	)
}