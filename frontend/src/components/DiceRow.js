import React from 'react';
import Die from './Die';

export default class DiceRow extends React.Component {
	render() {
		return (
			<div class="diceRow">
				{ this.props.dice.map((die) => (
					<Die face={die}></Die>
				))}
			</div>
		)
	}
}