from service.BaseHandler import BaseHandler
from service.MetaGameHandler import MetaGameHandler

class DisconnectionHandler(BaseHandler):
	async def handle_disconnect(self):
		try:
			client_id = await self.db.client_id_for_connection(self.connection)
			self.logger.info(f"Handling disconnect of {client_id}")

			games = await self.db.client_games(client_id)
			for game_id in games:
				handler = MetaGameHandler(self.db, self.comms, self.connection)
				await handler.fetch_game(game_id)
				await handler.leave_game(client_id)

			await self.db.remove_connection(self.connection)

			self.logger.info(f"Handled disconnect of {client_id}")
		except Exception as e:
			self.logger.warn(f"Exception while handling disconnect: {e}")
			raise e
