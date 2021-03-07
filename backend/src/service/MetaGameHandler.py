import json
from service.BaseHandler import GameHandler, ok_message, error_message
from service.GameState import GameState

class MetaGameHandler(GameHandler):
	"""Handles everything about the game/room, except the game play."""

	def clients_message(self, host):
		return json.dumps({
			"game_id": self.game.game_id,
			"type": "clients",
			"clients": list(self.clients.keys()),
			"host": host
		})

	async def send_clients_event(self, host):
		"""Sends event with all connected clients (human players and observers)"""
		message = self.clients_message(host)
		await self.broadcast(message)

	def bots_message(self, bots):
		return json.dumps({
			"game_id": self.game.game_id,
			"type": "bots",
			"bots": list(bots.keys()),
		})

	async def send_bots_event(self):
		"""Sends event with all bots"""
		bots = await self.game.bots()
		message = self.bots_message(bots)
		await self.broadcast(message)

	async def send_chat(self, client_id, message):
		message = json.dumps({
			"type": "chat",
			"client_id": client_id,
			"message": message
		})
		await self.broadcast(message)

	async def join_game(self, client_id, client_connection):
		await self.game.add_client(client_id, client_connection)
		self.clients[client_id] = client_connection

		host = await self.game.host()
		if host is None:
			host = client_id
			await self.game.set_host(host)

		await self.send_clients_event(host)

	async def leave_game(self, client_id):
		await self.game.remove_client(client_id)
		del self.clients[client_id]

		host = await self.game.host()
		if client_id == host:
			if self.clients:
				# Assign an (arbitrary) new host
				host = list(self.clients.keys())[0]
			else:
				host = None
			await self.game.set_host(host)

		await self.send_clients_event(host)

	async def send_status(self):
		host = await self.game.host()
		await self.send_message(self.clients_message(host))

		bots = await self.game.bots()
		await self.send_message(self.bots_message(bots))

		game_state = await self.game.state()
		if game_state:
			await self.send_message(self.game_state_message(game_state, []))

	async def next_bot_name(self):
		next_bot_id = await self.game.next_bot_id()
		bot_name = f"Bot #{next_bot_id}"
		await self.game.set_next_bot_id(next_bot_id + 1)

		return bot_name

	async def add_bot(self, bot_behaviour):
		await self.check_can_configure_game("add bot")

		bot_name = await self.next_bot_name()
		await self.game.add_bot(bot_name, bot_behaviour)

		self.logger.info(f"Added bot {bot_name}")
		await self.send_bots_event()

	async def remove_bot(self, bot_name):
		await self.check_can_configure_game("remove bot")

		await self.game.remove_bot(bot_name)

		self.logger.info(f"Removed bot {bot_name}")
		await self.send_bots_event()

	async def handle_game_command(self, cmd_message):
		cmd = cmd_message["action"]

		if cmd == "chat":
			return await self.send_chat(self.client_id, cmd_message["message"])

		if cmd == "send-status":
			return await self.send_status()

		if cmd == "join-game":
			return await self.join_game(self.client_id, self.connection)

		if cmd == "leave-game":
			return await self.leave_game(self.client_id)

		if cmd == "add-bot":
			return await self.add_bot(cmd_message["bot_behaviour"])

		if cmd == "remove-bot":
			return await self.remove_bot(cmd_message["bot_name"])

		self.logger.warn(f"Urecognized command {cmd}")
