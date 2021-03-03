Done:
-	Display actual scores
-	Skip sleep when throw does not contain tanks
- 	Fix layout sizes
- 	Show turn result => Bust, Scored: X
-	After player picked dice, show throw without selected dice
-	Fix size of top row in game area (via adaptive max size retention)
-	Add database API
	-	InMemoryDb implementation
-	Add game creation
-	Re-introduced animation delays
-	Removed "needless" delays
-	Add GameRoom component

TODO:
-	Add delays when no tanks in throw, but turn ends
-	Let player header reflect turnState
-	UI:
	-	Add top-level Connection React component
	-	Add ability to join game
	-	End game visualisation (ranking + Exit Game button)
	-	Avoid die overflows. Show only seven tanks/rays at most, with overflow indication.
-	Host at AWS
	-	DynamoDb implementation
-	Make Room IDs random four characters
-	Chat API
-	Improve play animations:
	-	Animate die addition/removal
-	Improve button colors
