import asyncio
import itertools
import json
import jsonpickle
import websockets
import logging
import random
from game.DataTypes import TurnState, TurnPhase, DieFace
from game.Game import RandomPlayer, DefensivePlayer
from game.OptimalPlay import OptimalActionSelector
from service.GameState import GameState
from service.InMemoryDb import InMemoryDb

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

def error_message(details):
	return json.dumps({
		"status": "error",
		"details": details
	})

def ok_message(info = {}):
	return json.dumps({
		"status": "ok",
		**info
	})

class GameServer:

	def __init__(self, db = None):
		self.db = db or InMemoryDb()

	async def register(self, client_id, websocket):
		if await self.db.has_client(client_id):
			return False

		await self.db.add_client(client_id, websocket)
		return True

	async def unregister(self, client_id):
		await self.db.remove_client(client_id)

	async def next_game_id(self):
		game_id = await self.db.next_game_id()
		await self.db.set_next_game_id(game_id + 1)
		return game_id

	async def main(self, websocket, path):
		registered = False
		while not registered:
			client_id = await websocket.recv()
			logger.info(f"Client joined: {client_id}")

			# Avoid possible bot name clash here, as this check is cheap
			if client_id.startswith("Bot-"):
				await websocket.send(error_message("Cannot join server. Name reserved for bots"))
			else:
				if await self.register(client_id, websocket):
					await websocket.send(ok_message())
					registered = True
				else:
					await websocket.send(error_message("Cannot join server. Name already in use"))

		try:
			async for message in websocket:
				logger.info(f"Message received: {message}")
				action = json.loads(message)

				if action["action"] == "create-game":
					game_id = await self.next_game_id()
					game = await self.db.create_game(game_id)
					await websocket.send(ok_message({ "game_id": game_id }))
					# Let action_handler handle rest of game set-up
				else:
					game_id = action["game_id"]
					game = self.db.game(game_id)

				action_handler = await GameActionHandler.create(game, client_id, websocket)
				await action_handler.handle_action(action)
		finally:
			await self.unregister(client_id)


class GameActionHandler:

	@staticmethod
	async def create(game, client_id, client_connection):
		# Fetch it already, as it is definitely needed, and sometimes more than once
		clients = await game.clients()

		return GameActionHandler(game, client_id, client_connection, clients)

	def __init__(self, game, client_id, client_connection, clients):
		self.game = game
		self.client_id = client_id
		self.client_connection = client_connection
		self.clients = clients

	async def send_clients_event(self, host):
		"""Sends event with all connected clients (human players and observers)"""
		if self.clients:
			message = json.dumps({
				"game_id": self.game.game_id,
				"type": "clients",
				"clients": list(self.clients.keys()),
				"host": host
			})
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	def bots_message(self, bots):
		return json.dumps({
			"game_id": self.game.game_id,
			"type": "bots",
			"bots": list(bots.keys()),
		})

	async def send_bots_event(self):
		"""Sends event with all bots"""
		if self.clients:
			bots = await self.game.bots()
			message = self.bots_message(bots)
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	def game_state_message(self, game_state, turn_state_transitions):
		return jsonpickle.encode({
			"game_id": self.game.game_id,
			"type": "game-state",
			"state": game_state,
			"turn_state_transitions": turn_state_transitions
		}, unpicklable = False)

	async def broadcast(self, message):
		if self.clients:
			print("broadcasting:", message)
			await asyncio.wait([ws.send(message) for ws in self.clients.values()])

	async def check_is_host(self, action):
		# Fetch here. It should not be needed elsewhere
		host = await self.game.host()

		if host != self.client_id:
			raise ClientException(f"{self.client_id} tried to {action}, but is not the host")

	async def check_is_recruiting(self, action):
		# Fetch here. It should be unset, so will not be re-used elsewhere
		game_state = await self.game.state()

		if game_state:
			raise ClientException(f"Can only {action} when game did not yet start")

	async def check_can_configure_game(self, action):
		await self.check_is_host(action)
		await self.check_is_recruiting(action)

	def check_expect_move(self, game_state):
		if game_state is None or not game_state.awaitsInput:
			raise ClientException(f"Not awaiting a move")

	def check_my_move(self, game_state):
		self.check_expect_move(game_state)
		if game_state.active_player != self.client_id:
			raise ClientException(f"{self.client_id} tried to move while it's not their turn")

	def check_bot_move(self, game_state, bots):
		self.check_expect_move(game_state)
		if not game_state.active_player in bots:
			raise ClientException("Bot move initiated while it's not a bot's turn")

	async def update_state_until_blocked(self, game_state):
		turn_state_transitions = [game_state.turn_state]
		while not (game_state.done or game_state.awaitsInput):
			game_state.next()
			turn_state_transitions.append(game_state.turn_state)

		await self.game.set_state(game_state)
		await self.broadcast(self.game_state_message(game_state, turn_state_transitions))

	async def start_game(self):
		await self.check_can_configure_game("start game")

		logger.info("Starting game")
		bots = await self.game.bots()
		game_state = GameState( itertools.chain(self.clients.keys(), bots.keys()) )

		await self.update_state_until_blocked(game_state)

	async def handle_move(self, game_state, input_value):
		game_state.next(input_value)

		await self.update_state_until_blocked(game_state)

	async def player_move(self, action):
		game_state = await self.game.state()
		self.check_my_move(game_state)

		if "pick-die" in action:
			picked = action["pick-die"].lower()
			if not picked in str2die:
				raise ClientException(f"Unknown die: {picked}")

			die = str2die[picked]
			if not game_state.turn_state.can_select(die):
				raise ClientException(f"Cannot select: {picked}")

			player_move = die
		elif "throw-again" in action:
			player_move = not action["throw-again"]
		else:
			raise ClientException("Unknown move")

		await self.handle_move(game_state, player_move)

	async def bot_move(self):
		await self.check_is_host("initiate bot move")

		game_state = await self.game.state()
		bots = await self.game.bots()
		self.check_bot_move(game_state, bots)
		
		action_selector = bots[game_state.active_player]

		turn_state = game_state.turn_state
		if turn_state.phase == TurnPhase.PickDice:
			bot_move = action_selector.select_die(turn_state)
		else:
			bot_move = action_selector.should_stop(turn_state)

		await self.handle_move(game_state, bot_move)

	async def register(self, client_id, client_connection):
		await self.game.add_client(client_id, client_connection)
		self.clients[client_id] = client_connection

		host = await self.game.host()
		if host is None:
			host = client_id
			await self.game.set_host(host)

		await self.send_clients_event(host)

	async def unregister(self, client_id):
		await self.game.remove_client[client_id]
		del self.clients[client_id]

		host = await self.game.host()
		if client_id == host:
			if self.clients:
				# Assign an (arbitrary) new host
				host = list(self.clients.keys())[0]
			else:
				host = None
			await self.game.set_host(host)

		await self.send_clients_event(host)

	async def next_bot_name(self):
		next_bot_id = await self.game.next_bot_id()
		bot_name = f"Bot #{next_bot_id}"
		await self.game.set_next_bot_id(next_bot_id + 1)

		return bot_name

	async def add_bot(self, bot_behaviour):
		await self.check_can_configure_game("add bot")

		bot_name = await self.next_bot_name()
		bot = bot_behaviours[bot_behaviour]
		await self.game.add_bot(bot_name, bot)

		logger.info(f"Added bot {bot_name}")
		await self.send_bots_event()

	async def remove_bot(self, bot_name):
		await self.check_can_configure_game("remove bot")

		await self.game.remove_bot(bot_name)

		logger.info(f"Removed bot {bot_name}")
		await self.send_bots_event()

	async def handle_action(self, action):
		print("handle_action", action)
		try:
			cmd = action["action"]
			if cmd == "chat":
				# TODO
				return

			if cmd == "create-game" or action ["action"] == "join-game":
				return await self.register(self.client_id, self.client_connection)

			if cmd == "leave-game":
				return await self.unregister(self.client_id)

			if cmd == "add-bot":
				return await self.add_bot(action["bot_behaviour"])

			if cmd == "remove-bot":
				return await self.remove_bot(action["bot_name"])

			if cmd == "start-game":
				return await self.start_game()
	
			if cmd == "move":
				return await self.player_move(action)

			if cmd == "bot-move":
				return await self.bot_move()

			logger.warn("Unrecognized action command:", cmd)
		except ClientException as e:
			logger.warn(e.message)

if __name__ == '__main__':
	game_server = GameServer()
	start_server = websockets.serve(game_server.main, "localhost", 8765)

	asyncio.get_event_loop().run_until_complete(start_server)
	asyncio.get_event_loop().run_forever()
