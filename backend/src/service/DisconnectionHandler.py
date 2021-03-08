from service.BaseHandler import BaseHandler
from service.MetaGameHandler import MetaGameHandler

class DisconnectionHandler(BaseHandler):
	async def handle_disconnect(self):
		try:
			self.logger.info(f"Handling disconnect of Connection {self.connection}")
			room_id = self.db.room_for_connection(self.connection)

			if room_id:
				handler = MetaGameHandler(self.db, self.comms, self.connection)
				handler.fetch_game(room_id)
				await handler.leave_room()

			self.logger.info(f"Handled disconnect of Connection {self.connection}")
		except Exception as e:
			self.logger.warn(f"Exception while handling disconnect: {e}")
