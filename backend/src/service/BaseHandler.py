import asyncio
import json
import jsonpickle
import logging

logger = logging.getLogger('handlers')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def error_message(details):
	return json.dumps({
		"type": "response",
		"status": "error",
		"details": details
	})

def ok_message(info = {}):
	return json.dumps({
		"type": "response",
		"status": "ok",
		**info
	})

class HandlerException(Exception):
	def __init__(self, message):
		self.message = message

class BaseHandler:
	def __init__(self, db, comms, connection):
		self.db = db
		self.comms = comms
		self.connection = connection
		self.logger = logger

	async def send_message(self, message):
		return await self.comms.send(self.connection, message)

	async def send_error_message(self, details):
		return await self.send_message(error_message(details))

class GameHandler(BaseHandler):

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
			await asyncio.wait([self.comms.send(ws, message) for ws in self.clients.values()])

	def check_is_host(self, action):
		# Fetch here. It should not be needed elsewhere
		host = self.game.host()

		if host != self.client_id:
			raise ClientException(f"{self.client_id} tried to {action}, but is not the host")

	async def check_is_recruiting(self, action):
		# Fetch here. It should be unset, so will not be re-used elsewhere
		game_state = await self.game.state()

		if game_state:
			raise HandlerException(f"Can only {action} when game did not yet start")

	async def check_can_configure_game(self, action):
		self.check_is_host(action)
		await self.check_is_recruiting(action)

	async def handle_game_command(self, cmd_message):
		pass

	async def fetch_game(self, game_id):
		self.game = self.db.game(game_id)

		if self.game:
			# Fetch these already, as they are definitely needed, and sometimes more than once
			self.client_id = await self.db.client_id_for_connection(self.connection)
			self.clients = await self.game.clients()

	async def handle_command(self, cmd_message):
		try:
			await self.fetch_game(cmd_message["game_id"])

			await self.handle_game_command(cmd_message)
		except Exception as e:
			self.logger.warn(e)
			raise e