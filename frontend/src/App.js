import './App.css';
import { AbductionZone } from './components/AbductionZone';
import { BattleZone } from './components/BattleZone';
import { DiceThrow } from './components/DiceThrow';
import { GameInfo } from './components/GameInfo';
import { PlayerList } from './components/PlayerList';

function App() {
	const diceThrow = {"tank": 2, "ray": 3, "human": 1, "chicken": 1, "cow": 0};
	const earthlings = { "human": 2, "cow": 4 };
	const combatants = { tank: 3, ray: 2 };
	const players = ["Alice", "Bob", "Charlie"];
	const scores = {"Alice": 7, "Bob": 4, "Charlie": 5};
	
	return (
    	<div className="App">
  			<div class="GameArea">
				<GameInfo round={2} turn="Bob" throw={4}></GameInfo>
				<DiceThrow throw={diceThrow}></DiceThrow>
				<BattleZone combatants={combatants}></BattleZone>
				<AbductionZone earthlings={earthlings}></AbductionZone>
			</div>
			<div class="PlayersArea">
				<PlayerList players={players} scores={scores}></PlayerList>
			</div>
		</div>
	);
}

export default App;
