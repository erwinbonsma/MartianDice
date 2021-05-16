import asyncio
import json
import jsonpickle
import logging
import traceback
from enum import IntEnum

logger = logging.getLogger('handlers')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class ErrorCode(IntEnum):
	UnspecifiedError = 0
	RoomNotFound = 1
	InvalidClientName = 2
	NameAlreadyPresent = 3
	PlayerLimitReached = 4
	InternalServerError = 255


def error_message(details, error_code = ErrorCode.UnspecifiedError):
	return json.dumps({
		"type": "response",
		"status": "error",
		"error_code": error_code,
		"details": details
	})

def ok_message(info = {}):
	return json.dumps({
		"type": "response",
		"status": "ok",
		**info
	})

class HandlerException(Exception):
	def __init__(self, message, error_code = ErrorCode.UnspecifiedError):
		self.message = message
		self.error_code = error_code

class BaseHandler:
	def __init__(self, db, comms, connection):
		self.db = db
		self.comms = comms
		self.connection = connection
		self.logger = logger

	async def send_message(self, message, dest_client = None):
		if dest_client:
			connection = [conn for conn, name in self.clients.items() if name == dest_client]
			if len(connection) == 0:
				self.logger.warn(f"No connection found for client {dest_client}")
				return
			destination = connection[0]
		else:
			destination = self.connection
		return await self.comms.send(destination, message)

	async def send_error_message(self, details, error_code = ErrorCode.UnspecifiedError):
		return await self.send_message(error_message(details, error_code))

class GameHandler(BaseHandler):

	def game_state_message(self, game_state, turn_state_transitions = []):
		return jsonpickle.encode({
			"game_id": self.room.game_id,
			"game_count": self.room.game_count,
			"type": "game-state",
			"state": game_state,
			"turn_state_transitions": turn_state_transitions
		}, unpicklable = False)

	async def broadcast(self, message):
		if self.clients:
			print("broadcasting:", message)
			await asyncio.wait([self.comms.send(ws, message) for ws in self.clients])

	def check_is_host(self, action):
		host = self.room.host()

		if host != self.client_id:
			raise HandlerException(f"{self.client_id} tried to {action}, but {host} is the host")

	def check_is_recruiting(self, action):
		pass

	def check_can_configure_game(self, action):
		self.check_is_host(action)
		self.check_is_recruiting(action)

	async def handle_game_command(self, cmd_message):
		pass

	def fetch_room(self, room_id):
		self.room = self.db.room_access(room_id)

		if self.room.exists():
			self.clients = self.room.clients()
			self.client_id = self.clients.get(self.connection, None)
			if self.client_id is None:
				self.logger.warn(f"No client ID for connection {self.connection}. #clients={len(self.clients)}")
			return True

	async def handle_command(self, cmd_message):
		room_id = cmd_message["room_id"] if "room_id" in cmd_message else cmd_message["game_id"]
		try:
			if not self.fetch_room(room_id):
				raise HandlerException(
					f"Room {room_id} not found",
					ErrorCode.RoomNotFound
				)

			await self.handle_game_command(cmd_message)
		except HandlerException as e:
			self.logger.warn(e.message)
			return await self.send_error_message(e.message, error_code = e.error_code)
		except Exception as e:
			self.logger.warn(e)
			traceback.print_exc()
			raise e