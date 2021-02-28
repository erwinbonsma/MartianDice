const reasons ={
	"No selectable dice": "Cannot select a die",
	"Defeated": "Defeated!",
	"No more dice": "No more dice remain",
	"Cannot improve score": "Cannot improve score",
	"Player choice": "Player ended turn"
};

export function TurnResult(props) {
	return (<div>
		{reasons[props.end_cause] || props.end_cause}<br></br>
		Score: {props.score}
	</div>);
}