import json
import logging
from service.DisconnectionHandler import DisconnectionHandler
from service.GamePlayHandler import GamePlayHandler
from service.MetaGameHandler import MetaGameHandler
from service.RegistrationHandler import RegistrationHandler
#from service.MemcachedStorage import MemcachedStorage
from service.DynamoDbStorage import DynamoDbStorage

logger = logging.getLogger('gateway')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class LocalGateway:
	def __init__(self):
		self.db = DynamoDbStorage()
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
					cmd_handler = RegistrationHandler(self.db, self.comms, socket_id)
				elif cmd == "start-game" or cmd == "move" or cmd == "bot-move":
					cmd_handler = GamePlayHandler(self.db, self.comms, socket_id)
				else:
					cmd_handler = MetaGameHandler(self.db, self.comms, socket_id)

				await cmd_handler.handle_command(cmd_message)
		except Exception as e:
			self.logger.info(e)
			raise e
		finally:
			del self.sockets[socket_id]
			await DisconnectionHandler(self.db, self.comms, socket_id).handle_disconnect()
