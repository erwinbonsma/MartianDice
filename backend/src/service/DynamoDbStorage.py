import boto3
from datetime import datetime, timedelta
import hashlib
import logging
import traceback
from service.GameState import GameState

logger = logging.getLogger('dynamodb')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

DEFAULT_CLIENT = boto3.client('dynamodb')
ROOM_EXPIRATION = timedelta(days = 1)

def room_ttl():
	return str(int((datetime.now() + ROOM_EXPIRATION).timestamp()))

class DynamoDbStorage:

	def __init__(self, client = DEFAULT_CLIENT):
		self.client = client

	def room_access(self, room_id):
		return DynamoDbRoom(room_id, self.client)

	def create_room(self, room_id):
		"""
		Tries to create a room with the given ID. On success, returns the room access wrapper.
		Returns None if creation failed.
		"""
		try:
			self.client.put_item(
				TableName = "rooms",
				Item = {
					"PKEY": { "S": f"Room#{room_id}" },
					"SKEY": { "S": "Instance" },
					"TTL": { "N": room_ttl() }
				},
				ConditionExpression = "attribute_not_exists(PKEY)"
			)
			return DynamoDbRoom(room_id, self.client)
		except Exception as e:
			logger.warn(f"Failed to create Room {room_id}: {e}")

	def set_room_for_connection(self, connection, room_id):
		try:
			response = self.client.put_item(
				TableName = "rooms",
				Item = {
					"PKEY": { "S": f"Conn#{connection}" },
					"SKEY": { "S": "Instance" },
					"RoomId": { "S": room_id }
				},
				ReturnValues = "ALL_OLD"
			)

			if "Attributes" in response:
				old_room = response["Attributes"]["RoomId"]["S"]
				logger.warn(f"Replaced room {old_room} for Connection {connection} by {room_id}")
			return True
		except Exception as e:
			logger.warn(f"Failed to set room for connection {connection}: {e}")

	def room_for_connection(self, connection):
		try:
			response = self.client.get_item(
				TableName = "rooms",
				Key = {
					"PKEY": { "S": f"Conn#{connection}" },
					"SKEY": { "S": "Instance" }
				}
			)

			if "Item" in response:
				return response["Item"]["RoomId"]["S"]
		except Exception as e:
			logger.warn(f"Failed to get room for connection {connection}: {e}")

	def clear_room_for_connection(self, connection):
		try:
			response = self.client.delete_item(
				TableName = "rooms",
				Key = {
					"PKEY": { "S": f"Conn#{connection}" },
					"SKEY": { "S": "Instance" }
				},
			)
		except Exception as e:
			logger.warn(f"Failed to clear room for connection {connection}: {e}")

class DynamoDbRoom:

	def __init__(self, room_id, client):
		self.room_id = room_id
		self.client = client

		self.__items = None
		self.__bots = None
		self.__clients = None
		self.__game_state_hash = None

	@property
	def game_id(self):
		return self.room_id

	def __instance_item(self):
		for item in self.__items:
			if item["SKEY"]["S"] == "Instance":
				return item

	def exists(self):
		"""
		Checks if the Room exists. This should be invoked first. This access wrapper can only be
		used when it returns True
		"""
		try:
			response = self.client.query(
				TableName = "rooms",
				KeyConditionExpression = "PKEY = :pkey",
				ExpressionAttributeValues = {
					":pkey": { "S": f"Room#{self.room_id}" }
				}
			)

			self.__items = response["Items"]
			print(f"Data for room {self.room_id}:", self.__items)

			return len(self.__items) > 0
		except Exception as e:
			logger.warn(f"Failed to check existence of Room {self.room_id}: {e}")

	def host(self):
		instance = self.__instance_item()
		if "Host" in instance:
			return instance["Host"]["S"]

	def clear_host(self):
		logger.info(f"Clearing host for Room {self.room_id}")
		try:
			self.client.update_item(
				TableName = "rooms",
				Key = {
					"PKEY": { "S": f"Room#{self.room_id}" },
					"SKEY": { "S": "Instance" }
				},
				UpdateExpression = "REMOVE #Host",
				ExpressionAttributeNames = {
					"#Host": "Host"
				}
			)

			del self.__instance_item()["Host"]
		except Exception as e:
			logger.warn(f"Failed to clear host for Room {self.room_id}: {e}")

	def set_host(self, host, old_host = None):
		if old_host:
			logger.info(f"Changing host for Room {self.room_id} from {old_host} to {host}")
			opt_values = { ":old_host": { "S": old_host } }
		else:
			logger.info(f"Setting host for Room {self.room_id} to {host}")
			opt_values = {}

		try:
			self.client.update_item(
				TableName = "rooms",
				Key = {
					"PKEY": { "S": f"Room#{self.room_id}" },
					"SKEY": { "S": "Instance" }
				},
				UpdateExpression = "SET #Host = :host",
				ExpressionAttributeNames = {
					"#Host": "Host"
				},
				ExpressionAttributeValues = {
					":host": { "S": host },
					**opt_values
				},
				ConditionExpression = "#Host = :old_host" if old_host else "attribute_not_exists(#Host)"
			)

			self.__instance_item()["Host"] = { "S": host }
			return host
		except Exception as e:
			logger.warn(f"Failed to set host for Room {self.room_id} to {host}: {e}")

	def clients(self):
		if self.__clients is None:
			self.__clients = {}
			for item in self.__items:
				skey = item["SKEY"]["S"]
				if skey.startswith("Conn#"):
					self.__clients[skey[5:]] = item["ClientId"]["S"]

		return self.__clients

	def add_client(self, connection, client_id):
		try:
			self.client.put_item(
				TableName = "rooms",
				Item = {
					"PKEY": { "S": f"Room#{self.room_id}" },
					"SKEY": { "S": f"Conn#{connection}" },
					"ClientId": { "S": client_id },
					"TTL": { "N": room_ttl() }
				},
				ConditionExpression = "attribute_not_exists(PKEY)"
			)

			clients = self.clients()
			clients[connection] = client_id

			return clients
		except Exception as e:
			logger.warn(f"Failed to add Client {client_id} to Room {self.room_id}: {e}")

	def remove_client(self, connection):
		try:
			response = self.client.delete_item(
				TableName = "rooms",
				Key = {
					"PKEY": { "S": f"Room#{self.room_id}" },
					"SKEY": { "S": f"Conn#{connection}" }
				}
			)

			clients = self.clients() # Ensure it is fetched
			del clients[connection]

			return clients
		except Exception as e:
			logger.warn(f"Failed to remove Connection {connection} from Room {self.room_id}: {e}")

	def __fetch_game_state(self):
		if self.__game_state_hash is not None:
			return # Already fetched it

		instance = self.__instance_item()

		if not "GameState" in instance:
			self.__game_state = None
			return # Nothing to fetch

		self.__game_state_hash = instance["GameState"]["S"]
		try:
			response = self.client.get_item(
				TableName = "games",
				Key = {
					"PKEY": { "S": self.__game_state_hash }
				},
			)

			pickled = response["Item"]["GameState"]["S"]
			self.__game_state = GameState.from_json(pickled)

		except Exception as e:
			logger.warn(f"Failed to get game state {self.__game_state_hash} for Room {self.room_id}: {e}")

	def set_game_state(self, game_state):
		old_hash = self.__game_state_hash
		opt_values = {}

		if old_hash is not None:
			game_state.set_from_hash(old_hash)
			opt_values = { ":old_hash": { "S": old_hash } }

		pickled = game_state.as_json()
		new_hash = hashlib.md5(pickled.encode('utf-8')).hexdigest()

		try:
			self.client.put_item(
				TableName = "games",
				Item = {
					"PKEY": { "S": new_hash },
					"GameState": { "S": pickled }
				}
			)

			self.client.update_item(
				TableName = "rooms",
				Key = {
					"PKEY": { "S": f"Room#{self.room_id}" },
					"SKEY": { "S": "Instance" }
				},
				UpdateExpression = "SET GameState = :new_hash",
				ExpressionAttributeValues = {
					":new_hash": { "S": new_hash },
					**opt_values
				},
				ConditionExpression = "GameState = :old_hash" if old_hash else "attribute_not_exists(GameState)"
			)

			self.__game_state = game_state
			self.__game_state_hash = new_hash

			return game_state
		except Exception as e:
			logger.warn(f"Failed to update game state from {old_hash} to {new_hash} for Room {self.room_id}: {e}")

	def game_state(self):
		self.__fetch_game_state()
		
		return self.__game_state
