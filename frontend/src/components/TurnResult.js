const reasons ={
	"No selectable dice": "Cannot select a die",
	"Defeated": "Defeated!",
	"No more dice": "No more dice remain",
	"Cannot improve score": "Cannot improve score",
	"Player choice": "Player ended turn"
};

export function TurnResult(props) {
	return (<center><p>
		{ reasons[props.end_cause] || props.end_cause }
		{ props.score > 0 && (<>. Scored {props.score} point{props.score && "s"}</>) }
	</p></center>);
}