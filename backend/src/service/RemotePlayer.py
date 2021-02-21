import asyncio
from game.DataTypes import DieFace, RoundState

str2die = {
	"ray": DieFace.Ray,
	"chicken": DieFace.Chicken,
	"cow": DieFace.Cow,
	"human": DieFace.Human
}

class RemotePlayer:

	def __init__(self, logger):
		self.queue = asyncio.Queue()
		self.logger = logger

	async def handle_action(self, action):
		await self.queue.put(action)

	async def select_die(self, state: RoundState):
		while True:
			action = await self.queue.get()
			if "pick-die" in action:
				picked = action["pick-die"].lower()
				if not picked in str2die:
					self.logger.info(f"Unknown die: {picked}")
					continue
				die = str2die[picked]
				if not state.can_select(die):
					self.logger.info(f"Cannot select: {picked}")
					continue
				print("Selected:", die)
				return die

	async def should_stop(self, state: RoundState):
		while True:
			action = await self.queue.get()
			if "throw-again" in action:
				return not action["throw-again"]

	def __str__(self):
		return "RemotePlayer"
