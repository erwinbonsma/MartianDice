import React from 'react';

export default class Die extends React.Component {
	render() {
		const imageFile = this.props.face + ".png";
		return (
			<div class="die">
				<img src={imageFile} width="75" height="75" alt="{props.face"></img>
			</div>
		)
	}
}