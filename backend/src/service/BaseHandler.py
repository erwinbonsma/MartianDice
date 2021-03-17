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
			await asyncio.wait([self.comms.send(ws, message) for ws in self.clients])

	def check_is_host(self, action):
		# Fetch here. It should not be needed elsewhere
		host = self.game.host()

		if host != self.client_id:
			raise HandlerException(f"{self.client_id} tried to {action}, but {host} is the host")

	def check_is_recruiting(self, action):
		# Fetch here. It should be unset, so will not be re-used elsewhere
		game_state = self.game.state()

		if game_state and not game_state.done:
			raise HandlerException(f"Can only {action} when no game is in progress")

	def check_can_configure_game(self, action):
		self.check_is_host(action)
		self.check_is_recruiting(action)

	async def handle_game_command(self, cmd_message):
		pass

	def fetch_game(self, game_id):
		self.game = self.db.room_access(game_id)

		if self.game.exists():
			self.clients = self.game.clients()
			self.client_id = self.clients.get(self.connection, None)
			return True

	async def handle_command(self, cmd_message):
		try:
			if not self.fetch_game(cmd_message["game_id"]):
				return await self.send_error_message("Room not found")

			await self.handle_game_command(cmd_message)
		except Exception as e:
			self.logger.warn(e)
			raise e