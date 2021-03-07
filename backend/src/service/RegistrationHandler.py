import random
from service.BaseHandler import BaseHandler, ok_message, error_message

def create_game_id():
	return ''.join(chr(random.randint(ord('A'), ord('Z'))) for _ in range(4))

class RegistrationHandler(BaseHandler):

	async def handle_join(self, cmd_message):
		if await self.db.has_connection(self.connection):
			return self.logger.warn("Client already registered")

		client_id = cmd_message["client_id"]

		# Avoid possible bot name clash here, as this check is cheap
		if client_id.startswith("Bot-"):
			return await self.send_error_message("Sorry, but that is restricted to non-sentients")

		if await self.db.has_client(client_id):
			return await self.send_error_message("Sorry, that name has been claimed already")

		await self.db.add_connection(self.connection, client_id)
		await self.send_message(ok_message({ "client_id": client_id }))

	async def handle_create_game(self):
		attempts = 0
		while attempts < 4:
			game_id = create_game_id()
			print(game_id)
			game = await self.db.create_game(game_id)
			if game:
				return await self.send_message(ok_message({ "game_id": game_id }))

			attempts += 1
		
		raise RuntimeError("Failed to generate a unique Game ID")

	async def handle_command(self, cmd_message):
		cmd = cmd_message["action"]

		if cmd == "join":
			return await self.handle_join(cmd_message)
		if cmd == "create-game":
			return await self.handle_create_game()

		self.logger.warn(f"Unrecognized command {cmd}")
