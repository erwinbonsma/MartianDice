import boto3
import json
import logging
from service.DisconnectionHandler import DisconnectionHandler
from service.GamePlayHandler import GamePlayHandler
from service.MetaGameHandler import MetaGameHandler
from service.RegistrationHandler import RegistrationHandler
from service.DynamoDbStorage import DynamoDbStorage

logger = logging.getLogger('gateway')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

game_cmds = {"start-game", "move", "bot-move", "end-turn", "remove-player"}

class LocalGateway:
	def __init__(self):
		self.db = DynamoDbStorage(
			client = boto3.client('dynamodb', endpoint_url="http://dynamodb:8000")
		)
		self.comms = self
		self.logger = logger

		self.next_socket_id = 1
		self.sockets = {}

	async def send(self, socket_id, message):
		socket = self.sockets.get(socket_id, None)
		if socket:
			await socket.send(message)

	async def main(self, websocket, path):
		socket_id = str(self.next_socket_id)
		self.sockets[socket_id] = websocket
		self.next_socket_id += 1

		try:
			async for message in websocket:
				self.logger.info(f"Message received: {message}")
				cmd_message = json.loads(message)
				cmd = cmd_message["action"]

				if cmd == "create-room":
					cmd_handler_class = RegistrationHandler
				elif cmd in game_cmds:
					cmd_handler_class = GamePlayHandler
				else:
					cmd_handler_class = MetaGameHandler
				cmd_handler = cmd_handler_class(self.db, self.comms, socket_id)

				await cmd_handler.handle_message(cmd_message)
		except Exception as e:
			self.logger.info(e)
			raise e
		finally:
			del self.sockets[socket_id]
			await DisconnectionHandler(self.db, self.comms, socket_id).handle_disconnect()
