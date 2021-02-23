import asyncio
import itertools
import json
import websockets
import logging
import random
from game.DataTypes import TurnState, TurnPhase
from game.Game import play_turn_async, RandomPlayer, DefensivePlayer
from game.OptimalPlay import OptimalActionSelector
from service.GameState import GameState, GamePhase
from service.RemotePlayer import RemotePlayer

logger = logging.getLogger('websockets.server')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

bot_behaviours = {
	"random": RandomPlayer(),
	"defensive": DefensivePlayer(),
	"smart": OptimalActionSelector()
}

class ClientException(Exception):
	def __init__(self, message):
		self.message = message

class AsyncBotWrapper:
	def __init__(self, action_selector):
		self.action_selector = action_selector

	async def select_die_async(self, state: TurnState):
		return self.action_selector.select_die(state)

	async def should_stop_async(self, state: TurnState):
		return self.action_selector.should_stop(state)

class GameServer:

	def __init__(self):
		self.clients = {} # Contains players as well as observers
		self.bots = {}
		self.game_state = GameState()
		self.host = None
		self.next_bot_id = 1

	def clients_event(self):
		"""Sends event with all connected clients (human players and observers)"""
		return json.dumps({
			"type": "clients",
			"clients": list(self.clients.keys()),
			"host": self.host
		})

	async def send_clients_event(self):
		if self.clients:
			message = self.clients_event()
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	async def broadcast(self, message):
		if self.clients:
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	def start_game(self):
		self.game_state.start_game(itertools.chain(self.clients.keys(), self.bots.keys()))
		self.start_turn()

	def update_turn_state(self, turn_state):
		if self.game_state.turn_state is None:
			self.game_state.start_turn(turn_state)

		if turn_state.phase == TurnPhase.Done:
			logger.info(f"{turn_state.score} points scored in round")
			self.game_state.end_turn()

		asyncio.get_event_loop().create_task(self.broadcast(self.game_state.as_json()))

		if turn_state.phase == TurnPhase.Done:
			if self.game_state.next_turn():
				self.start_turn()
			else:
				asyncio.get_event_loop().create_task(self.broadcast(self.game_state.as_json()))

	async def play_turn(self):
		await play_turn_async(self.move_handler, state_listener = self.update_turn_state)

	def start_turn(self):
		player_id = self.game_state.active_player
		logger.info(f"Player {player_id} starts turn")
		if player_id in self.bots:
			self.move_handler = AsyncBotWrapper(self.bots[player_id])
		else:
			self.move_handler = RemotePlayer(logger)
		# Execute turn in background. It should not block the current client's event loop
		asyncio.get_event_loop().create_task(self.play_turn())

	async def register(self, client_id, websocket):
		if client_id in self.clients or client_id in self.bots:
			return False

		self.clients[client_id] = websocket
		if self.host is None:
			self.host = client_id # First client becomes the host

		await self.send_clients_event()
		return True

	async def unregister(self, client_id):
		del self.clients[client_id]
		if client_id == self.host:
			if len(self.clients) == 0:
				# Close game when last client leaves
				asyncio.get_event_loop().stop()
			else:
				# Assign an (arbitrary) new host
				self.host = list(self.clients.keys())[0]

		await self.send_clients_event()

	def next_bot_name(self):
		while True:
			bot_name = f"Bot #{self.next_bot_id}"
			self.next_bot_id += 1
			if not bot_name in self.clients:
				return bot_name

	def check_is_host(self, client_id, action):
		if self.host != client_id:
			raise ClientException(f"{client_id} tried to {action}, but is not the host")

	def check_is_recruiting(self, action):
		if self.game_state.phase != GamePhase.Recruiting:
			raise ClientException(f"Can only {action} when recruiting")

	def check_is_active_player(self, client_id):
		if self.game_state.active_player != client_id:
			raise ClientException(f"{client_id} tried to move while it's not their turn")

	async def handle_action(self, client_id, action):
		try:
			if action["action"] == "chat":
				# TODO
				return

			if action["action"] == "add-bot":
				self.check_is_host(client_id, "add bot")
				self.check_is_recruiting("add bot")

				bot_name = self.next_bot_name()
				self.bots[bot_name] = bot_behaviours[action["bot_behaviour"]]
				logger.info(f"Added bot {bot_name}")

			if action["action"] == "remove-bot":
				self.check_is_host(client_id, "remove bot")
				self.check_is_recruiting("remove bot")

				bot_name = action["bot_name"]
				del self.bots[bot_name]
				logger.info(f"Removed bot {bot_name}")

			if action["action"] == "start-game":
				self.check_is_host(client_id, "start game")
				self.check_is_recruiting("start game")

				self.start_game()
	
			if action["action"] == "move":
				self.check_is_active_player(client_id)

				await self.move_handler.handle_action(action)
		except ClientException as e:
			logger.warn(e.message)

	async def main(self, websocket, path):
		client_id = await websocket.recv()
		logger.info(f"Client joined: {client_id}")

		if not await self.register(client_id, websocket):
			await websocket.send("Cannot join game. Name already taken")
			await websocket.close()
			return

		try:
			async for message in websocket:
				logger.info("Message received:", message)
				action = json.loads(message)
				if action["action"] == "leave_game": break
				await self.handle_action(client_id, action)
		finally:
			await self.unregister(client_id)

game_server = GameServer()
start_server = websockets.serve(game_server.main, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
