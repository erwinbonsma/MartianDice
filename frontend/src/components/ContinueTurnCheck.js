import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function ContinueTurnCheck(props) {
	return (
		<Container>
			<Row>
				<Col sm={6}>Continue turn?</Col>
				<Col><Button id="yes" onClick={props.onAnswer}>Yes</Button></Col>
				<Col><Button id="no" onClick={props.onAnswer}>No</Button></Col>
			</Row>
		</Container>
	)
}