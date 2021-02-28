Messages (incoming):
- createGame(clientName)
	- Sends: clientUpdate
- joinGame(clientName, gameId)
	- Sends: clientUpdate
- addBot(gameId, botBehaviour)
	- Restriction: Host
	- Sends: botUpdate
- removeBot(gameId, botName)
	- Restriction: Host
	- Sends: botUpdate
- disconnect
	- Sends: clientUpdate(s)
- startGame(gameId)
	- Sends: gameUpdate
- sendMessage(gameId, message)
- move(gameId, move) 

Messages (outgoing):
- clientUpdate(gameId, clients, host)
	- Note: Updates host if needed
- botUpdate(gameId, bots)
- gameUpdate(gameId, players, activePlayer, turnState?, round, scores, done)

Database:
- gameId => Host: clientName
- gameId => Clients: clientName, connectionId
- gameId => Bots: botName, botBehaviour
- gameId => GameState: JSON