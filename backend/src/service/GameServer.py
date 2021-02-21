import asyncio
import json
import websockets
import logging
import random
from game.DataTypes import RoundState, RoundPhase
from game.Game import play_round_async, RandomPlayer, DefensivePlayer
from game.OptimalPlay import OptimalActionSelector
from service.GameState import GameState
from service.RemotePlayer import RemotePlayer

logger = logging.getLogger('websockets.server')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

players = {
	100: "Alice",
	200: "Bob"
}

bots = {
	300: ("Randy", RandomPlayer()),
	301: ("Dee", DefensivePlayer()),
	302: ("Max", OptimalActionSelector())
}

games = {
	1000: {
		"players": [100, 200],
		"bots": []
	},
	2000: {
		"players": [100],
		"bots": []
	},
	3000: {
		"players": [100],
		"bots": [300, 301, 302]
	}
}

class AsyncBotWrapper:
	def __init__(self, action_selector):
		self.action_selector = action_selector

	async def select_die_async(self, state: RoundState):
		return self.action_selector.select_die(state)

	async def should_stop_async(self, state: RoundState):
		return self.action_selector.should_stop(state)

class GameServer:

	def __init__(self, game_id = 2000):
		self.game_id = game_id
		self.players = {}
		self.bots = set(games[game_id]["bots"])
		self.expected_players = set(games[game_id]["players"])

	def players_event(self):
		return json.dumps({"type": "players", "count": len(self.players)})

	async def send_players_event(self):
		if self.players:
			message = self.players_event()
			await asyncio.wait([ws.send(message) for ws in self.players.values()])

	async def broadcast(self, message):
		if self.players:
			await asyncio.wait([ws.send(message) for ws in self.players.values()])

	async def start_game(self):
		self.game_state = GameState(list(self.players.keys()) + list(self.bots))
		self.start_round()

	def update_round_state(self, round_state):
		self.game_state.round_state = round_state
		if round_state.phase == RoundPhase.Done:
			score = round_state.score()
			logger.info(f"{score} points scored in round")
			self.game_state.end_round(score)

		asyncio.get_event_loop().create_task(self.broadcast(self.game_state.as_json()))

		if round_state.phase == RoundPhase.Done:
			if self.game_state.next_round():
				self.start_round()
			else:
				asyncio.get_event_loop().create_task(self.broadcast(self.game_state.as_json()))

	async def play_new_round(self):
		await play_round_async(self.move_handler, state_listener = lambda state: self.update_round_state(state))

	def start_round(self):
		player_id = self.game_state.active_player
		logger.info(f"Start round with player {player_id}")
		if player_id in self.bots:
			self.move_handler = AsyncBotWrapper(bots[player_id][1])
		else:
			self.move_handler = RemotePlayer(logger)
		asyncio.get_event_loop().create_task(self.play_new_round())

	async def register(self, player_id, websocket):
		self.players[player_id] = websocket
		self.expected_players.remove(player_id)
		await self.send_players_event()
		if len(self.expected_players) == 0:
			await self.start_game()

	async def unregister(self, player_id):
		del self.players[player_id]
		self.expected_players.add(player_id)
		await self.send_players_event()
		if len(self.players) == 0 and self.game_state.done:
			asyncio.get_event_loop().stop()

	async def main(self, websocket, path):
		player_id = int(await websocket.recv())
		logger.info(f"Player ID: {player_id}")
		if not player_id in self.expected_players:
			websocket.close()
			return

		await self.register(player_id, websocket)
		try:
			async for message in websocket:
				action = json.loads(message)
				print(action)
				if action["action"] == "exit_game":
					break
				elif action["action"] == "chat":
					pass
				elif action["action"] == "move":
					if self.game_state.active_player != player_id:
						await asyncio.wait(websocket.send("It's not your turn"))
					else:
						await self.move_handler.handle_action(action)
		finally:
			await self.unregister(player_id)

game_server = GameServer(3000)
start_server = websockets.serve(game_server.main, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
