import './App.css';
import Die from './components/Die';
import DiceRow from './components/DiceRow';

function App() {
	const dice = ["tank", "tank", "ray", "human", "chicken", "cow"];
	
	return (
    	<div className="App">
  			<header className="App-header">
				<Die face="human"></Die><Die face="cow"></Die>
				<DiceRow dice={dice}></DiceRow>
			</header>
		</div>
	);
}

export default App;
