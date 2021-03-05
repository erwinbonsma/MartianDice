class NonExistantGame:
	async def clients(self):
		return None

NON_EXISTANT_GAME = NonExistantGame()

class InMemoryGame:
	def __init__(self, game_id):
		self.__game_id = game_id
		self.__bots = {}
		self.__clients = {}
		self.__host = None
		self.__state = None
		self.__next_bot_id = 1

	@property
	def game_id(self):
		return self.__game_id

	async def add_bot(self, bot_id, bot):
		self.__bots[bot_id] = bot

	async def remove_bot(self, bot_id):
		del self.__bots[bot_id]

	async def bots(self):
		return dict(self.__bots)

	async def set_next_bot_id(self, next_id):
		self.__next_bot_id = next_id

	async def next_bot_id(self):
		return self.__next_bot_id

	async def add_client(self, client_id, client_connection):
		self.__clients[client_id] = client_connection

	async def remove_client(self, client_id):
		del self.__clients[client_id]

	async def clients(self):
		return dict(self.__clients)

	async def set_state(self, state):
		self.__state = state

	async def state(self):
		return self.__state

	async def host(self):
		return self.__host

	async def set_host(self, host):
		self.__host = host

class InMemoryDb:
	def __init__(self):
		self.__clients = {}
		self.__games = {}
		self.__next_game_id = "1"

	def game(self, game_id):
		return self.__games.get(game_id, NON_EXISTANT_GAME)

	async def has_client(self, client_id):
		return client_id in self.__clients

	async def add_client(self, client_id, client_connection):
		self.__clients[client_id] = client_connection

	async def remove_client(self, client_id):
		del self.__clients[client_id]

	async def clients(self):
		return self.__clients

	async def create_game(self, game_id):
		new_game = InMemoryGame(game_id)
		self.__games[game_id] = new_game
		return new_game

	async def next_game_id(self):
		return self.__next_game_id

	async def set_next_game_id(self, next_id):
		self.__next_game_id = next_id
