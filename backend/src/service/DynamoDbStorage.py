import boto3
import logging

logger = logging.getLogger('dynamodb')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

DEFAULT_CLIENT = boto3.client('dynamodb', endpoint_url="http://dynamodb:8000")

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
					"PKEY": {
						"S": f"Room#{room_id}"
					},
					"SKEY": {
						"S": "Instance"
					}
				},
				ConditionExpression = "attribute_not_exists(PKEY)"
			)
			return DynamoDbRoom(room_id, self.client)
		except Exception as e:
			logger.warn(f"Failed to create Room {room_id}: {e}")

	def set_room_for_connection(self, connection, room_id):
		try:
			response = self.client.put_item(
				Item={
					"PKEY": {
						"S": f"Conn#{connection}"
					},
					"SKEY": {
						"S": "Instance"
					},
					"RoomId": {
						"S": room_id
					}
				},
				TableName="rooms",
				ReturnValues="ALL_OLD"
			)
			if "RoomId" in response["Attributes"]:
				old_room = response["Attributes"]["RoomId"]["S"]
				logger.warn(f"Replaced room {old_room} for Connection {connection} by {room_id}")
			return True
		except Exception as e:
			logger.warn(f"Failed to set room for connection {connection}: {e}")
			print(e)
			print(e.message)

	def room_for_connection(self, connection):
		try:
			response = self.client.get_item(
				TableName = "rooms",
				Key = {
					"PKEY": {
						"S": f"Conn#{connection}"
					},
					"SKEY": {
						"S": "Instance",
					}
				},
				ReturnConsumedCapacity = "NONE"
			)

			if "Item" in response:
				return response["Item"]["RoomId"]
		except Exception as e:
			logger.warn(f"Failed to get room for connection {connection}: {e}")

	def clear_room_for_connection(self, connection):
		try:
			response = self.client.delete_item(
				TableName = "rooms",
				Key = {
					"PKEY": {
						"S": f"Conn#{connection}"
					},
					"SKEY": {
						"S": "Instance",
					}
				},
				ReturnConsumedCapacity = "NONE"
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
					":pkey": {
						"S": f"Room#{self.room_id}"
					}
				},
				ReturnConsumedCapacity = "NONE"
			)

			self.__items = response["Items"]
			print(self.__items)

			return len(self.__items) > 0
		except Exception as e:
			logger.warn(f"Failed to check existence of Room {self.room_id}: {e}")

	def host(self):
		instance = self.__instance_item()
		if "Host" in instance:
			return instance["Host"]["S"]

	def set_host(self, host):
		try:
			self.client.update_item(
				TableName = "rooms",
				Key = {
					"PKEY": {
						"S": f"Room#{self.room_id}"
					},
					"SKEY": {
						"S": "Instance"
					}
				},
				UpdateExpression = "SET Host = :host",
				ExpressionAttributeValues = {
					":host": {
						"S": host,
					}
				},
				ConditionExpression = "attribute_not_exists(Host)"
			)

			self.__instance_item()["Host"] = { "S": host }
		except:
			logger.warn(f"Failed to set host for Room {self.room_id} to {host}: {e}")

	def next_bot_id(self):
		try:
			response = self.client.update_item(
				TableName = "rooms",
				Key = {
					"PKEY": {
						"S": f"Room#{self.room_id}"
					},
					"SKEY": {
						"S": "Instance"
					}
				},
				UpdateExpression = "ADD NextBotId :inc",
				ExpressionAttributeValues = {
					":inc": {
						"N": "1"
					}
				},
				ReturnValues = "UPDATED_NEW"
			)

			return int(response["Attributes"]["NextBotId"]["N"])
		except Exception as e:
			logger.warn(f"Failed to update NextBotId for Room {self.room_id}: {e}")

	def bots(self):
		if self.__bots is None:
			self.__bots = {}
			for item in self.__items:
				skey = item["SKEY"]["S"]
				if skey.startswith("Bot#"):
					self.__bots[skey[4:]] = item["Behaviour"]["S"]

			print("bots =", self.__bots)
		return self.__bots

	def add_bot(self, bot_name, bot_behaviour):
		try:
			self.client.put_item(
				TableName = "rooms",
				Item = {
					"PKEY": {
						"S": f"Room#{self.room_id}"
					},
					"SKEY": {
						"S": f"Bot#{bot_name}"
					},
					"Behaviour": {
						"S": bot_behaviour
					}
				},
				ConditionExpression = "attribute_not_exists(PKEY)"
			)

			bots = self.bots() # Ensure it is fetched
			bots[bot_name] = bot_behaviour

			return bots
		except Exception as e:
			logger.warn(f"Failed to add bot {bot_name} in room {self.room_id}: {e}")

	def remove_bot(self, bot_name):
		try:
			response = self.client.delete_item(
				TableName = "rooms",
				Key = {
					"PKEY": {
						"S": f"Room#{self.room_id}"
					},
					"SKEY": {
						"S": f"Bot#{bot_name}"
					},
				}
			)

			bots = self.bots() # Ensure it is fetched
			del bots[bot_name]

			return bots
		except Exception as e:
			logger.warn(f"Failed to remove bot {bot_name} from room {self.room_id}: {e}")

	def clients(self):
		if self.__clients is None:
			self.__clients = {}
			for item in self.__items:
				skey = item["SKEY"]["S"]
				if skey.startswith("Client#"):
					self.__clients[item["Connection"]["S"]] = skey[7:]

			print("clients =", self.__clients)
		return self.__clients

	def add_client(self, connection, client_id):
		try:
			self.client.put_item(
				TableName = "rooms",
				Item = {
					"PKEY": {
						"S": f"Room#{self.room_id}"
					},
					"SKEY": {
						"S": f"Client#{client_id}"
					},
					"Connection": {
						"S": connection
					}
				},
				ConditionExpression = "attribute_not_exists(PKEY)"
			)

			clients = self.clients()
			clients[connection] = client_id

			return self.clients
		except:
			logger.warn(f"Failed to add client {client_id} in Room {self.room_id}: {e}")

	def state(self):
		pass
