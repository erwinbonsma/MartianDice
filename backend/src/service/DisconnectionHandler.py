from service.BaseHandler import BaseHandler
from service.MetaGameHandler import MetaGameHandler

class DisconnectionHandler(BaseHandler):
	async def handle_disconnect(self):
		try:
			self.logger.info("Handling disconnect of Connection %s", self.connection)
			room_id = self.db.room_for_connection(self.connection)

			if room_id:
				handler = MetaGameHandler(self.db, self.comms, self.connection)
				handler.fetch_room(room_id)
				await handler.leave_room()

			self.logger.info("Handled disconnect of Connection %s", self.connection)
		except Exception as e:
			self.logger.warn("Exception while handling disconnect: %s", str(e))
