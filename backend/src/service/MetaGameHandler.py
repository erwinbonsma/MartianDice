import json
from service.BaseHandler import GameHandler, HandlerException, ok_message
from service.GamePlayHandler import bot_behaviours
from service.GameState import GameState

MAX_NAME_LENGTH = 12
MAX_CLIENTS_PER_ROOM = 6
MAX_BOTS_PER_ROOM = 6

class MetaGameHandler(GameHandler):
	"""Handles everything about the game/room, except the game play."""

	def clients_message(self, host):
		return json.dumps({
			"game_id": self.game.game_id,
			"type": "clients",
			"clients": list(self.clients.values()),
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

	async def send_bots_event(self, bots):
		"""Sends event with all bots"""
		message = self.bots_message(bots)
		await self.broadcast(message)

	async def send_chat(self, message):
		message = json.dumps({
			"type": "chat",
			"client_id": self.client_id,
			"message": message
		})
		await self.broadcast(message)

	async def join_room(self, room_id, client_id):
		# Avoid possible bot name clash here, as this check is cheap
		if client_id.startswith("Bot-"):
			raise HandlerException(f"Name {client_id} is restricted to non-sentients")

		if len(client_id) == 0 or len(client_id) > MAX_NAME_LENGTH:
			raise HandlerException("Invalid name length")

		if client_id in self.clients.values():
			raise HandlerException(f"Name {client_id} already present in Room {room_id}")

		if len(self.clients) >= MAX_CLIENTS_PER_ROOM:
			raise HandlerException(f"Room {room_id} is at its player capacity limit")

		if not self.db.set_room_for_connection(self.connection, room_id):
			raise HandlerException(f"Failed to link connection to Room {room_id}")

		updated_clients = self.game.add_client(self.connection, client_id)
		if updated_clients is None:
			raise HandlerException("Failed to join game. Please try again")
		self.clients = updated_clients

		host = self.game.host()
		if host is None:
			host = client_id
			self.game.set_host(host)

		await self.send_clients_event(host)

	async def leave_room(self):
		attempts = 0
		# Retry removal. It can fail if two (or more clients) disconnect at the same time. In that
		# case, CAS ensures that (at least) one update succeeded so removal should eventually
		# succeed. Note, in contrast to join_game, cannot make client responsible for retrying, as
		# it will typically have disconnected.
		while attempts < 4:
			updated_clients = self.game.remove_client(self.connection)
			if updated_clients is not None:
				break
			attempts += 1
			await asyncio.sleep(random.random() * attempts)

		if updated_clients is None:
			return self.logger.error(f"Failed to remove {self.client_id} from game {self.game.game_id}")
		self.clients = updated_clients

		self.db.clear_room_for_connection(self.connection)

		host = self.game.host()
		if self.client_id == host:
			if self.clients:
				# Assign an (arbitrary) new host
				host = self.game.set_host(list(self.clients.values())[0], old_host = host)
			else:
				host = None
				self.game.clear_host()

		await self.send_clients_event(host)

	async def send_status(self):
		host = self.game.host()
		await self.send_message(self.clients_message(host))

		bots = self.game.bots()
		await self.send_message(self.bots_message(bots))

		game_state = self.game.state()
		if game_state:
			await self.send_message(self.game_state_message(game_state, []))

	def next_bot_name(self):
		next_bot_id = self.game.next_bot_id()
		bot_name = f"Bot #{next_bot_id}"

		return bot_name

	async def add_bot(self, bot_behaviour):
		self.check_can_configure_game("add bot")

		if len(self.game.bots()) >= MAX_BOTS_PER_ROOM:
			raise HandlerException(f"Room {self.game.game_id} is at its bot capacity limit")

		if not bot_behaviour in bot_behaviours:
			raise HandlerException(f"Unknown bot behaviour '{bot_behaviour}'")

		bot_name = self.next_bot_name()
		bots = self.game.add_bot(bot_name, bot_behaviour)

		if bots is not None:
			self.logger.info(f"Added bot {bot_name}")
			await self.send_bots_event(bots)

	async def remove_bot(self, bot_name):
		self.check_can_configure_game("remove bot")

		bots = self.game.remove_bot(bot_name)

		if bots is not None:
			self.logger.info(f"Removed bot {bot_name}")
			await self.send_bots_event(bots)

	async def handle_game_command(self, cmd_message):
		cmd = cmd_message["action"]

		if cmd == "chat":
			return await self.send_chat(cmd_message["message"])

		if cmd == "send-status":
			return await self.send_status()

		if cmd == "join-room":
			return await self.join_room(cmd_message["game_id"], cmd_message["client_id"])

		if cmd == "leave-room":
			return await self.leave_room()

		if cmd == "add-bot":
			return await self.add_bot(cmd_message["bot_behaviour"])

		if cmd == "remove-bot":
			return await self.remove_bot(cmd_message["bot_name"])

		self.logger.warn(f"Urecognized command {cmd}")
