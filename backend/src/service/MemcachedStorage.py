import json
import jsonpickle
import logging
from pymemcache.client import base

logger = logging.getLogger('backend.memcached')

DEFAULT_EXPIRY = 3600

class JsonSerde(object):
	def serialize(self, key, value):
		if isinstance(value, str):
			return value.encode('utf-8'), 1
		return jsonpickle.encode(value).encode('utf-8'), 2

	def deserialize(self, key, value, flags):
		if flags == 1:
			return value.decode('utf-8')
		if flags == 2:
			return jsonpickle.decode(value.decode('utf-8'))
		raise Exception("Unknown serialization format")

DEFAULT_CLIENT = base.Client('memcached', serde = JsonSerde(), default_noreply = False)

class MemcachedStorage:

	def __init__(self, cache_client = DEFAULT_CLIENT):
		self.cache_client = cache_client

	def room_access(self, room_id):
		return MemcachedRoom(room_id, self.cache_client)

	def create_room(self, room_id):
		"""
		Tries to create a room with the given ID. On success, returns the room access wrapper.
		Returns None if creation failed.
		"""
		room = MemcachedRoom(room_id, self.cache_client)
		if room.exists():
			logger.warn(f"Cannot create Room {room_id}. It already exists")
		elif room._set_initial_state():
			return room

	def set_room_for_connection(self, connection, room_id):
		key = f"Con#{connection}"
		existing_room_id = self.cache_client.get(key)
		if existing_room_id:
			logger.warn(f"Connection {connection} already has Room {existing_room_id} linked to it")
		else:
			return self.cache_client.set(key, room_id, expire = DEFAULT_EXPIRY)

	def room_for_connection(self, connection):
		return self.cache_client.get(f"Con#{connection}")

	def clear_room_for_connection(self, connection):
		return self.cache_client.delete(f"Con#{connection}")

class MemcachedRoom:

	def __init__(self, room_id, cache_client):
		self.__room_id = room_id
		self.cache_client = cache_client

	@property
	def bots_key(self):
		return f"Room#{self.room_id}-bots"

	@property
	def clients_key(self):
		return f"Room#{self.room_id}-clients"

	@property
	def host_key(self):
		return f"Room#{self.room_id}-host"

	@property
	def next_bot_id_key(self):
		return f"Room#{self.room_id}-next_bot_id"

	@property
	def game_state_key(self):
		return f"Room#{self.room_id}-game_state"

	@property
	def room_id(self):
		return self.__room_id

	@property
	def game_id(self):
		return self.__room_id

	def _set_initial_state(self):
		failed = self.cache_client.set_many(dict([
			(self.room_id, "1"),
			(self.next_bot_id_key, "0"),
			(self.bots_key, {}),
			(self.clients_key, {}),
			(self.game_state_key, "")
		]), expire = DEFAULT_EXPIRY)

		if failed:
			logger.warn("Failed to create game. Failed to set:", failed)
		return len(failed) == 0

	def warn(self, msg):
		logger.warn(f"Warning [Room {self.room_id}]: {msg}")

	def exists(self):
		value = self.cache_client.get(self.room_id)
		return value is not None

	def add_bot(self, bot_id, bot):
		bots, cas = self.cache_client.gets(self.bots_key)
		bots[bot_id] = bot
		if self.cache_client.cas(self.bots_key, bots, cas, expire = DEFAULT_EXPIRY):
			return bots
		else:
			self.warn("CAS failed for add_bot")

	def remove_bot(self, bot_id):
		bots, cas = self.cache_client.gets(self.bots_key)
		if bot_id in bots:
			del bots[bot_id]
			if self.cache_client.cas(self.bots_key, bots, cas, expire = DEFAULT_EXPIRY):
				return bots
			else:
				self.warn("CAS failed for remove_bot")

	def bots(self):
		return self.cache_client.get(self.bots_key)

	def next_bot_id(self):
		next_id = self.cache_client.incr(self.next_bot_id_key, 1)
		if next_id is None:
			self.warn("INCR failed for next_bot_id")
		return next_id

	def add_client(self, connection, client_id):
		clients, cas = self.cache_client.gets(self.clients_key)
		clients[connection] = client_id
		if self.cache_client.cas(self.clients_key, clients, cas, expire = DEFAULT_EXPIRY):
			return clients
		else:
			self.warn("CAS failed for add_client")

	def remove_client(self, connection):
		clients, cas = self.cache_client.gets(self.clients_key)
		if connection in clients:
			del clients[connection]
			if self.cache_client.cas(self.clients_key, clients, cas, expire = DEFAULT_EXPIRY):
				return clients
			else:
				self.warn("CAS failed for remove_client")

	def clients(self):
		return self.cache_client.get(self.clients_key)

	def set_state(self, state):
		# Note: It should be practically impossible for the update to fail due to concurrency, as
		# only one client at any moment is allowed to update the state. However, it is could
		# conceivably occur, for example when clients (and services handling their request) have
		# (temporarily) inconsistent views of who is hosting the game. Better safe than sorry...
		if self.cache_client.cas(self.game_state_key, state, self.state_cas, expire = DEFAULT_EXPIRY):
			return state
		else:
			self.warn("CAS failed for set_state")

	def state(self):
		state, self.state_cas = self.cache_client.gets(self.game_state_key)
		return state

	def host(self):
		return self.cache_client.get(self.host_key)

	def set_host(self, host):
		if not self.cache_client.set(self.host_key, host, expire = DEFAULT_EXPIRY):
			self.warn("SET failed for host")
