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

class GameState:

	def __init__(self, counts = {}):
		self.__counts = dict(counts)

	def copy(self):
		return GameState(self.__counts)

	def num(self, die_face):
		return self.__counts.get(die_face, 0)

	def num_earthlings(self):
		return sum(self.num(key) for key in EARTHLINGS)

	def add(self, die_face, number):
		self.__counts[die_face] = self.num(die_face) + number

	def selectable_earthlings(self, throw):
		return [key for key in EARTHLINGS if self.num(key) == 0 and throw.num(key) > 0]

	def collected_earthlings(self):
		return [key for key in EARTHLINGS if self.num(key) > 0]

	def is_done(self, throw):
		selectable_earthlings = self.selectable_earthlings(throw)
		rays = throw.num(DieFace.Ray)
		if len(selectable_earthlings) == 0 and rays == 0:
			return True

		forced_earthlings = 0 if rays > 0 else min(throw.num(x) for x in selectable_earthlings)
		tanks = self.num(DieFace.Tank)
		max_rays = NUM_DICE - tanks - self.num_earthlings() - forced_earthlings

		return tanks > max_rays

	def total_collected(self):
		return sum(self.__counts.values())

	def update_tanks(self, throw):
		self.add(DieFace.Tank, throw.num(DieFace.Tank))

	def handle_choice(self, throw, selected):
		assert(throw.num(selected) > 0)
		assert(selected == DieFace.Ray or self.num(selected) == 0)
		self.add(selected, throw.num(selected))

	def score(self):
		if self.num(DieFace.Tank) > self.num(DieFace.Ray):
			return 0
		bonus = 3 if sum(1 for key in EARTHLINGS if self.num(key) > 0) == 3 else 0
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

	def num(self, die_face):
		return self.__counts.get(die_face, 0)

	def set_num(self, die_face, count):
		self.__counts[die_face] = count

	def __str__(self):
		return str(self.__counts)
