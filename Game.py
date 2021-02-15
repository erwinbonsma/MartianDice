from collections import namedtuple
from enum import IntEnum
from random import choice, randint, random

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

	def __init__(self):
		self.__counts = {}

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

	def __init__(self, num_dice):
		self.__counts = {}

		for die_throw in range(num_dice):
			die = randint(0, 5)
			if die > DieFace.Ray:
				die -= 1
			die_face = DieFace(die)
			self.__counts[die_face] = self.__counts.get(die_face, 0) + 1

	def num(self, die_face):
		return self.__counts.get(die_face, 0)

	def __str__(self):
		return str(self.__counts)

class RandomPlayer:

	def select_die(self, state, throw):
		options = state.selectable_earthlings(throw)
		if throw.num(DieFace.Ray) > 0:
			options.append(DieFace.Ray)
		return choice(options)

	def should_stop(self, state):
		return state.score() > 0 and random() > 0.5

	def __str__(self):
		return "RandomPlayer"

class DefensivePlayer:

	def select_die(self, state, throw):
		if throw.num(DieFace.Ray) > 0 and state.num(DieFace.Tank) > state.num(DieFace.Ray):
			return DieFace.Ray
		options = state.selectable_earthlings(throw)
		return choice(options) if len(options) > 0 else DieFace.Ray

	def should_stop(self, state):
		buffer = state.num(DieFace.Ray) - state.num(DieFace.Tank)
		return state.score() > 0 and (buffer < 2 or len(state.collected_earthlings()) == 3)

	def __str__(self):
		return "DefensivePlayer"

def random_throw(state):
	return DiceThrow(NUM_DICE - state.total_collected())

def play_game(action_selector, throw_fun = random_throw, state = None, trace = False):
	if state == None:
		state = GameState()

	while True:
		throw = throw_fun(state)
		if trace:
			print("Throw:", throw)

		state.update_tanks(throw)
		if state.is_done(throw):
			if trace:
				if state.score() > 0:
					print("Done!")
				else:
					print("Bust!")
			break

		selected_die = action_selector.select_die(state, throw)
		if trace:
			print("Selection:", selected_die)

		state.handle_choice(throw, selected_die)
		if trace:
			print("State:", state)

		if state.total_collected() == NUM_DICE or action_selector.should_stop(state):
			if trace:
				print("Stopping")
			break

	score = state.score()
	if trace:
		print("Score:", score)

	return score

if __name__ == '__main__':
	action_selector = DefensivePlayer()

	play_game(action_selector, trace = True)

	for player in [RandomPlayer(), DefensivePlayer()]:
		num_games = 100
		summed_score = sum(play_game(player) for _ in range(num_games))
		print("Average score of %s" % (player), summed_score / num_games)

