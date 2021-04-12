import asyncio
import json
import random
from service.BaseHandler import GameHandler, HandlerException, ok_message
from service.Config import Config
from service.GamePlayHandler import bot_behaviours
from service.GameState import GameState

class MetaGameHandler(GameHandler):
	"""Handles everything about the game/room, except the game play."""

	def clients_message(self):
		return json.dumps({
			"room_id": self.room.room_id,
			"type": "clients",
			"clients": list(self.clients.values()),
			"host": self.room.host()
		})

	async def send_clients_event(self):
		"""Sends event with all connected clients (human players and observers)"""
		message = self.clients_message()
		await self.broadcast(message)

	def game_config_message(self, game_config):
		return json.dumps({
			"room_id": self.room.room_id,
			"type": "game-config",
			"game_config": game_config,
		})

	async def send_game_config_event(self, game_config):
		"""Sends event with game configuration"""
		message = self.game_config_message(game_config)
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

		await self.send_clients_event()

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

		await self.send_clients_event()

	async def switch_host(self):
		game_state = self.room.game_state()
		if game_state is None:
			raise HandlerException("Can only switch host when game is in progress")
		if game_state.age_in_seconds < Config.MAX_MOVE_TIME_IN_SECONDS:
			raise HandlerException("Cannot switch host yet")

		self.room.set_host(self.client_id, old_host = self.room.host())
		await self.send_clients_event()

	async def send_welcome(self, to_clients, game_config, game_state):
		self.check_is_host("send welcome")

		for client in to_clients:
			await self.send_message(self.game_config_message(game_config), dest_client = client)
			if game_state is not None:
				await self.send_message(self.game_state_message(game_state), dest_client = client)

	async def send_clients(self):
		await self.send_message(self.clients_message())

	async def update_config(self, game_config):
		self.check_can_configure_game("update game config")

		# Sanity checks on configuration
		bots = game_config["bots"]
		if len(bots) > Config.MAX_BOTS_PER_ROOM:
			raise HandlerException(f"Room {self.room.room_id} cannot exceed bot capacity limit")

		for name, behaviour in bots.items():
			if not name.startswith("Bot-"):
				raise HandlerException(f"Invalid bot name '{name}'")
			if not behaviour in bot_behaviours:
				raise HandlerException(f"Unknown bot behaviour '{behaviour}'")

		# Share with other clients
		await self.send_game_config_event(game_config)

	async def handle_game_command(self, cmd_message):
		cmd = cmd_message["action"]

		if cmd == "chat":
			return await self.send_chat(cmd_message["message"])

		if cmd == "send-welcome":
			return await self.send_welcome(
				cmd_message["to_clients"],
				cmd_message["game_config"],
				cmd_message["game_state"] if "game_state" in cmd_message else None, 
			)

		if cmd == "send-clients":
			return await self.send_clients()

		if cmd == "join-room":
			return await self.join_room(cmd_message["room_id"], cmd_message["client_id"])

		if cmd == "leave-room":
			return await self.leave_room()

		if cmd == "switch-host":
			return await self.switch_host()

		if cmd == "update-config":
			return await self.update_config(cmd_message["game_config"])

		self.logger.warn(f"Unrecognized command {cmd}")
