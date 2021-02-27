export function TurnResult(props) {
	return (<div className="Row">
		Turn ended: {props.end_cause}, Score: {props.score}
	</div>);
}