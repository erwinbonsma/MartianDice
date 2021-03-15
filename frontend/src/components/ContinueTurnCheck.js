import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export function ContinueTurnCheck(props) {
	return (
		<Container>
			<Row>
				<Col sm={2} xs={0} />
				<Col sm={3} xs={5} ><Button id="yes" onClick={props.onAnswer} style={{width: "100%"}}>Yes</Button></Col>
				<Col sm={2} xs={2} />
				<Col sm={3} xs={5} ><Button id="no" onClick={props.onAnswer} style={{width: "100%"}}>No</Button></Col>
				<Col sm={2} xs={0}/>
			</Row>
		</Container>
	)
}