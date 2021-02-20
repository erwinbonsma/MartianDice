from enum import IntEnum
from random import randint

NUM_DICE = 13

class DieFace(IntEnum):
	Tank = 0
	Ray = 1
	Chicken = 2
	Cow = 3
	Human = 4

EARTHLINGS = (DieFace.Chicken, DieFace.Cow, DieFace.Human)

NUM_DIE_FACE_TYPES = 5

class RoundPhase(IntEnum):
	Throwing = 0
	PostThrow = 1
	PickDice = 2
	PostPick = 3
	CheckExit = 4
	Done = 5

class SideDiceState:

	def __init__(self, counts = {}):
		self.__counts = dict(counts)

	def copy(self):
		return SideDiceState(self.__counts)

	def __getitem__(self, die_face):
		return self.__counts.get(die_face, 0)

	def num_earthlings(self):
		return sum(self[key] for key in EARTHLINGS)

	def add(self, die_face, number):
		self.__counts[die_face] = self[die_face] + number

	def collected_earthlings(self):
		return [key for key in EARTHLINGS if self[key] > 0]

	def total_collected(self):
		return sum(self.__counts.values())

	def update_tanks(self, throw):
		self.add(DieFace.Tank, throw[DieFace.Tank])

	def handle_choice(self, throw, selected):
		assert(throw[selected] > 0)
		assert(selected == DieFace.Ray or self[selected] == 0)
		self.add(selected, throw[selected])

	def score(self):
		if self[DieFace.Tank] > self[DieFace.Ray]:
			return 0
		bonus = 3 if sum(1 for key in EARTHLINGS if self[key] > 0) == 3 else 0
		return self.num_earthlings() + bonus

	def __str__(self):
		return str(self.__counts)

class DiceThrow:

	def __init__(self, num_dice = 0):
		self.__counts = {}

		for die_throw in range(num_dice):
			die = randint(0, 5)
			if die > DieFace.Ray:
				die -= 1
			die_face = DieFace(die)
			self.__counts[die_face] = self.__counts.get(die_face, 0) + 1

	def num_dice(self):
		return sum(self.__counts.values())

	def __getitem__(self, die_face):
		return self.__counts.get(die_face, 0)

	def set_num(self, die_face, count):
		self.__counts[die_face] = count

	def __str__(self):
		return str(self.__counts)

class RoundState:

	def __init__(self, start_side_state = None):
		self.side_dice = start_side_state.copy() if start_side_state else SideDiceState()
		self.phase = RoundPhase.Throwing
		self.throw = None

	def score(self):
		return self.side_dice.score()

	def selectable_earthlings(self):
		return [key for key in EARTHLINGS if self.side_dice[key] == 0 and self.throw[key] > 0]

	def set_throw(self, throw):
		assert(self.phase == RoundPhase.Throwing)

		self.throw = throw
		self.phase = RoundPhase.PostThrow

	def check_post_throw_exit(self):
		assert(self.phase == RoundPhase.PostThrow)

		self.side_dice.update_tanks(self.throw)

		selectable_earthlings = self.selectable_earthlings()
		rays = self.throw[DieFace.Ray]
		if len(selectable_earthlings) == 0 and rays == 0:
			self.phase = RoundPhase.Done
			self.done_reason = "No selectable dice"
			return True

		forced_earthlings = 0 if rays > 0 else min(self.throw[x] for x in selectable_earthlings)
		tanks = self.side_dice[DieFace.Tank]
		max_rays = NUM_DICE - tanks - self.side_dice.num_earthlings() - forced_earthlings

		if tanks > max_rays:
			self.phase = RoundPhase.Done
			self.done_reason = "Defeated"
			return True

		self.phase = RoundPhase.PickDice

	def handle_pick(self, selected_die):
		assert(self.phase == RoundPhase.PickDice)
	
		self.last_pick = selected_die
		self.side_dice.handle_choice(self.throw, selected_die)
		self.phase = RoundPhase.PostPick

	def check_post_pick_exit(self):
		assert(self.phase == RoundPhase.PostPick)

		if self.side_dice.total_collected() == NUM_DICE:
			self.phase = RoundPhase.Done
			self.done_reason = "No more dice"
			return True

		if self.score() > 0 and len(self.side_dice.collected_earthlings()) == 3:
			self.phase = RoundPhase.Done
			self.done_reason = "Cannot improve score"
			return True

		self.phase = RoundPhase.CheckExit if self.score() > 0 else RoundPhase.Throwing

	def check_player_exit(self, stop):
		assert(self.phase == RoundPhase.CheckExit)

		if stop:
			self.phase = RoundPhase.Done
			self.done_reason = "Player choice"
			return True

		self.phase = RoundPhase.Throwing
