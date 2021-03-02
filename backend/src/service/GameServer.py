import asyncio
import itertools
import json
import websockets
import logging
import random
from game.DataTypes import TurnState, TurnPhase, DieFace
from game.Game import RandomPlayer, DefensivePlayer
from game.OptimalPlay import OptimalActionSelector
from service.GameState import GameState

logger = logging.getLogger('websockets.server')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logging.setLogRecordFactory(logging.LogRecord)

bot_behaviours = {
	"random": RandomPlayer(),
	"defensive": DefensivePlayer(),
	"smart": OptimalActionSelector()
}

str2die = {
	"ray": DieFace.Ray,
	"chicken": DieFace.Chicken,
	"cow": DieFace.Cow,
	"human": DieFace.Human
}

class ClientException(Exception):
	def __init__(self, message):
		self.message = message

def copy_state(game_state: GameState):
	# TODO: Do not copy here but make states immutable and switch to Redux
	as_json = game_state.as_json()
	# TODO: Calculate and add MD5
	return json.loads(as_json)

class GameServer:

	def __init__(self):
		self.clients = {} # Contains players as well as observers
		self.bots = {}
		self.game_state = None
		self.host = None
		self.next_bot_id = 1

	async def send_clients_event(self):
		"""Sends event with all connected clients (human players and observers)"""
		if self.clients:
			message = json.dumps({
				"type": "clients",
				"clients": list(self.clients.keys()),
				"host": self.host
			})
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	def bots_message(self):
		return json.dumps({
			"type": "bots",
			"bots": list(self.bots.keys()),
		})

	def states_message(self, states):
		return json.dumps({
			"type": "game-states",
			"states": states
		})

	async def send_bots_event(self):
		"""Sends event with all bots"""
		if self.clients:
			message = self.bots_message()
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	async def broadcast(self, message):
		if self.clients:
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	async def update_state_until_blocked(self):
		states = [copy_state(self.game_state)]
		while not (self.game_state.done or self.game_state.awaitsInput):
			self.game_state.next()
			states.append(copy_state(self.game_state))

		await self.broadcast(self.states_message(states))

	async def start_game(self):
		self.game_state = GameState(itertools.chain(self.clients.keys(), self.bots.keys()))

		await self.update_state_until_blocked()

	async def handle_move(self, input_value):
		self.game_state.next(input_value)

		await self.update_state_until_blocked()

	async def execute_player_move(self, action):
		if "pick-die" in action:
			picked = action["pick-die"].lower()
			if not picked in str2die:
				logger.info(f"Unknown die: {picked}")
				return
			die = str2die[picked]
			if not self.game_state.turn_state.can_select(die):
				logger.info(f"Cannot select: {picked}")
				return
			player_move = die
		elif "throw-again" in action:
			player_move = not action["throw-again"]
		else:
			logger.info("Unknown move")
			return

		await self.handle_move(player_move)

	async def execute_bot_move(self):
		action_selector = self.bots[self.game_state.active_player]

		state = self.game_state.turn_state
		if state.phase == TurnPhase.PickDice:
			bot_move = action_selector.select_die(state)
		else:
			bot_move = action_selector.should_stop(state)

		await self.handle_move(bot_move)

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
		if not self.game_state is None:
			raise ClientException(f"Can only {action} when game did not yet start")

	def check_expect_move(self):
		if self.game_state is None or not self.game_state.awaitsInput:
			raise ClientException(f"Not awaiting a move")

	def check_expect_move_from(self, client_id):
		self.check_expect_move()
		if self.game_state.active_player != client_id:
			raise ClientException(f"{client_id} tried to move while it's not their turn")

	def check_expect_move_from_bot(self):
		self.check_expect_move()
		if not self.game_state.active_player in self.bots:
			raise ClientException("Bot move initiated while it's not a bot's turn")

	async def handle_action(self, client_id, action):
		print("handle_action", action, self.game_state.as_json() if self.game_state else None)
		try:
			if action["action"] == "chat":
				# TODO
				return

			if action["action"] == "add-bot":
				self.check_is_host(client_id, "add bot")
				self.check_is_recruiting("add bot")

				bot_name = self.next_bot_name()
				self.bots[bot_name] = bot_behaviours[action["bot_behaviour"]]
				await self.send_bots_event()
				logger.info(f"Added bot {bot_name}")

			if action["action"] == "remove-bot":
				self.check_is_host(client_id, "remove bot")
				self.check_is_recruiting("remove bot")

				bot_name = action["bot_name"]
				del self.bots[bot_name]
				await self.send_bots_event()
				logger.info(f"Removed bot {bot_name}")

			if action["action"] == "start-game":
				self.check_is_host(client_id, "start game")
				self.check_is_recruiting("start game")

				await self.start_game()
				logger.info("Started game")
	
			if action["action"] == "move":
				self.check_expect_move_from(client_id)

				await self.execute_player_move(action)

			if action["action"] == "bot-move":
				self.check_is_host(client_id, "initiate bot move")
				self.check_expect_move_from_bot()

				await self.execute_bot_move()

		except ClientException as e:
			logger.warn(e.message)

	async def main(self, websocket, path):
		client_id = await websocket.recv()
		logger.info(f"Client joined: {client_id}")

		if not await self.register(client_id, websocket):
			await websocket.send("Cannot join game. Name already taken")
			await websocket.close()
			return
		await websocket.send(self.bots_message())

		try:
			async for message in websocket:
				logger.info(f"Message received: {message}")
				action = json.loads(message)
				if action["action"] == "leave_game": break
				await self.handle_action(client_id, action)
		finally:
			await self.unregister(client_id)

if __name__ == '__main__':
	game_server = GameServer()
	start_server = websockets.serve(game_server.main, "localhost", 8765)

	asyncio.get_event_loop().run_until_complete(start_server)
	asyncio.get_event_loop().run_forever()
