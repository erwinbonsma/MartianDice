import asyncio
import json
from service.BaseHandler import GameHandler, HandlerException, ok_message
from service.Config import Config
from service.GamePlayHandler import bot_behaviours
from service.GameState import GameState

class MetaGameHandler(GameHandler):
	"""Handles everything about the game/room, except the game play."""

	def clients_message(self, host):
		return json.dumps({
			"room_id": self.room.room_id,
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
			"room_id": self.room.room_id,
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

		if len(client_id) == 0 or len(client_id) > Config.MAX_NAME_LENGTH:
			raise HandlerException("Invalid name length")

		if client_id in self.clients.values():
			raise HandlerException(f"Name {client_id} already present in Room {room_id}")

		if len(self.clients) >= Config.MAX_CLIENTS_PER_ROOM:
			raise HandlerException(f"Room {room_id} is at its player capacity limit")

		if not self.db.set_room_for_connection(self.connection, room_id):
			raise HandlerException(f"Failed to link connection to Room {room_id}")

		updated_clients = self.room.add_client(self.connection, client_id)
		if updated_clients is None:
			raise HandlerException("Failed to join game. Please try again")
		self.clients = updated_clients

		host = self.room.host()
		if host is None:
			host = client_id
			self.room.set_host(host)

		await self.send_clients_event(host)

	async def leave_room(self):
		attempts = 0
		# Retry removal. It can fail if two (or more clients) disconnect at the same time. In that
		# case, CAS ensures that (at least) one update succeeded so removal should eventually
		# succeed. Note, in contrast to join_game, cannot make client responsible for retrying, as
		# it will typically have disconnected.
		while attempts < 4:
			updated_clients = self.room.remove_client(self.connection)
			if updated_clients is not None:
				break
			attempts += 1
			await asyncio.sleep(random.random() * attempts)

		if updated_clients is None:
			return self.logger.error(f"Failed to remove {self.client_id} from Room {self.room.room_id}")
		self.clients = updated_clients

		self.db.clear_room_for_connection(self.connection)

		host = self.room.host()
		if self.client_id == host:
			if self.clients:
				# Assign an (arbitrary) new host
				host = self.room.set_host(list(self.clients.values())[0], old_host = host)
			else:
				host = None
				self.room.clear_host()

		await self.send_clients_event(host)

	async def switch_host(self):
		game_state = self.room.game_state()
		if game_state is None:
			raise HandlerException("Can only switch host when game is in progress")
		if game_state.age_in_seconds < Config.MAX_MOVE_TIME_IN_SECONDS:
			raise HandlerException("Cannot switch host yet")

		host = self.room.set_host(self.client_id, old_host = self.room.host())
		await self.send_clients_event(host)

	async def send_status(self):
		host = self.room.host()
		await self.send_message(self.clients_message(host))

		bots = self.room.bots()
		await self.send_message(self.bots_message(bots))

		game_state = self.room.game_state()
		if game_state:
			await self.send_message(self.game_state_message(game_state, []))

	def next_bot_name(self):
		next_bot_id = self.room.next_bot_id()
		bot_name = f"Bot #{next_bot_id}"

		return bot_name

	async def add_bot(self, bot_behaviour):
		self.check_can_configure_game("add bot")

		if len(self.room.bots()) >= Config.MAX_BOTS_PER_ROOM:
			raise HandlerException(f"Room {self.room.room_id} is at its bot capacity limit")

		if not bot_behaviour in bot_behaviours:
			raise HandlerException(f"Unknown bot behaviour '{bot_behaviour}'")

		bot_name = self.next_bot_name()
		bots = self.room.add_bot(bot_name, bot_behaviour)

		if bots is not None:
			self.logger.info(f"Added bot {bot_name}")
			await self.send_bots_event(bots)

	async def remove_bot(self, bot_name):
		self.check_can_configure_game("remove bot")

		bots = self.room.remove_bot(bot_name)

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
			return await self.join_room(cmd_message["room_id"], cmd_message["client_id"])

		if cmd == "leave-room":
			return await self.leave_room()

		if cmd == "switch-host":
			return await self.switch_host()

		if cmd == "add-bot":
			return await self.add_bot(cmd_message["bot_behaviour"])

		if cmd == "remove-bot":
			return await self.remove_bot(cmd_message["bot_name"])

		self.logger.warn(f"Urecognized command {cmd}")
