import json
import logging
from service.DisconnectionHandler import DisconnectionHandler
from service.GamePlayHandler import GamePlayHandler
from service.MetaGameHandler import MetaGameHandler
from service.RegistrationHandler import RegistrationHandler
from service.InMemoryDb import InMemoryDb

logger = logging.getLogger('gateway')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class SocketCommunication:
	async def send(self, connection, message):
		await connection.send(message)

class LocalGateway:
	def __init__(self):
		self.db = InMemoryDb()
		self.comms = SocketCommunication()
		self.logger = logger

	async def main(self, websocket, path):
		try:
			async for message in websocket:
				self.logger.info(f"Message received: {message}")
				cmd_message = json.loads(message)
				cmd = cmd_message["action"]

				if cmd == "join" or cmd == "create-game":
					cmd_handler = RegistrationHandler(self.db, self.comms, websocket)
				elif cmd == "start-game" or cmd == "move" or cmd == "bot-move":
					cmd_handler = GamePlayHandler(self.db, self.comms, websocket)
				else:
					cmd_handler = MetaGameHandler(self.db, self.comms, websocket)

				await cmd_handler.handle_command(cmd_message)
		except Exception as e:
			self.logger.info(e)
			raise e
		finally:
			await DisconnectionHandler(self.db, self.comms, websocket).handle_disconnect()
