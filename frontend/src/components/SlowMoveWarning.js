import Button from 'react-bootstrap/Button';

export function SlowMoveWarning({ myTurn, onEndTurn }) {
	return <center className="Warning">{
		myTurn ? "Please make a move!"
		: <Button onClick={onEndTurn} size="sm">End turn</Button>
	}</center>
}