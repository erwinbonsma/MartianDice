
export function GameResult(props) {
	const ranked = Object.entries(props.game.scores).sort(
		(a, b) => b[1] - a[1]
	);
	const maxScore = ranked[0][1];

	return (<>
		<h4>Results</h4>
		<div style={{padding: "0 1em 0.2em"}}>
		{	ranked.map(result => {
				const playerName = result[0];
				const score = result[1];
				const textClassName = (score === maxScore) ? "Winner" : "";
				const barClassName = (score === maxScore) ? "ScoreBar-Winner" : "ScoreBar";
				return (<div key={result[0]} style={{display: "flex", justifyContent: "space-between", margin: "0.2em" }}>
					<div className={textClassName} style={{flexGrow: 10, flexBasis: 0, margin: "0 0.2em 0 0" }}>{playerName}</div>
					<div className={barClassName} style={{flexGrow: score, flexBasis: 0}}></div>
					<div className={textClassName} style={{flexGrow: 3 + (maxScore - score), flexBasis: 0, margin: "0 0 0 0.5em"}} >{score}</div>
				</div>);
			})
		}
		</div>
	</>)
}