const reasons ={
	"No selectable dice": "Cannot select a die",
	"Defeated": "Defeated!",
	"No more dice": "No more dice remain",
	"Cannot improve score": "Cannot improve score",
	"Player choice": "Player ended turn"
};

export function TurnResult({ score, endCause }) {
	return (<center>
		{ reasons[endCause] || endCause }
		{ score > 0 && (<>. Scored {score} point{score && "s"}</>) }
	</center>);
}