import json
from pymemcache.client import base

class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode('utf-8'), 1
        return json.dumps(value).encode('utf-8'), 2

    def deserialize(self, key, value, flags):
       if flags == 1:
           return value.decode('utf-8')
       if flags == 2:
           return json.loads(value.decode('utf-8'))
       raise Exception("Unknown serialization format")

cache_client = base.Client('memcached', serde = JsonSerde())

class InMemoryGame:
	def __init__(self, game_id, db):
		self.__game_id = game_id
		self.__db = db

		self.__bots = {}
		self.__clients = {}
		self.__state = None
		self.set_next_bot_id(1)

	@property
	def game_id(self):
		return self.__game_id

	async def add_bot(self, bot_id, bot):
		self.__bots[bot_id] = bot

	async def remove_bot(self, bot_id):
		del self.__bots[bot_id]

	async def bots(self):
		return dict(self.__bots)

	def set_next_bot_id(self, next_id):
		print("set_next_bot_id", next_id)
		return cache_client.set(f"{self.game_id}-next_bot_id", str(next_id))

	def next_bot_id(self):
		return int(cache_client.get(f"{self.game_id}-next_bot_id"))

	async def add_client(self, client_id, client_connection):
		self.__clients[client_id] = client_connection
		self.__db._add_client_to_game(client_id, self.game_id)

	async def remove_client(self, client_id):
		del self.__clients[client_id]
		self.__db._remove_client_from_game(client_id, self.game_id)

	async def clients(self):
		return dict(self.__clients)

	async def set_state(self, state):
		self.__state = state

	async def state(self):
		return self.__state

	def host(self):
		return cache_client.get(f"{self.game_id}-host")

	def set_host(self, host):
		cache_client.set(f"{self.game_id}-host", host)

class InMemoryDb:
	def __init__(self):
		self.__clients = {}
		self.__games = {}
		self.__games_for_client = {}
		self.__connections = {}

	async def has_connection(self, connection):
		return connection in self.__connections

	async def client_id_for_connection(self, connection):
		return self.__connections[connection]

	async def has_client(self, client_id):
		return client_id in self.__clients

	async def add_connection(self, connection, client_id):
		self.__clients[client_id] = connection
		self.__games_for_client[client_id] = set()
		self.__connections[connection] = client_id

	async def remove_connection(self, connection):
		client_id = self.__connections[connection]
		assert(len(self.__games_for_client[client_id]) == 0)
		del self.__connections[connection]
		del self.__clients[client_id]

	async def clients(self):
		return self.__clients

	async def client_games(self, client_id):
		return list(self.__games_for_client[client_id])

	def _add_client_to_game(self, client_id, game_id):
		self.__games_for_client[client_id].add(game_id)

	def _remove_client_from_game(self, client_id, game_id):
		self.__games_for_client[client_id].remove(game_id)

	async def create_game(self, game_id):
		"""Creates new game. Returns None if game with given ID already exists."""
		if game_id in self.__games:
			return None

		new_game = InMemoryGame(game_id, self)
		self.__games[game_id] = new_game
		return new_game

	def game(self, game_id):
		return self.__games.get(game_id, None)
