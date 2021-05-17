import random
from service.BaseHandler import BaseMessageHandler, ok_message, error_message

def create_room_id():
	return ''.join(chr(random.randint(ord('A'), ord('Z'))) for _ in range(4))

class RegistrationHandler(BaseMessageHandler):

	async def create_room(self):
		attempts = 0
		while attempts < 4:
			room_id = create_room_id()
			room_access = self.db.create_room(room_id)
			if room_access:
				return await self.send_message(ok_message({ "room_id": room_id }))

			attempts += 1
		
		raise RuntimeError("Failed to create room")

	async def _handle_message(self, cmd_message):
		cmd = cmd_message["action"]

		if cmd == "create-room":
			return await self.create_room()

		self.logger.warn(f"Unrecognized command {cmd}")
