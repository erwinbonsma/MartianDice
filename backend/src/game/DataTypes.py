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

class TurnPhase(IntEnum):
	Throwing = 0
	Thrown = 1
	PickDice = 2
	PostPick = 3
	ThrowAgain = 4
	Done = 5

class SideDiceState:

	def __init__(self, counts = {}):
		self.__counts = counts

	@property
	def score(self):
		if self[DieFace.Tank] > self[DieFace.Ray]:
			return 0
		bonus = 3 if sum(1 for key in EARTHLINGS if self[key] > 0) == 3 else 0
		return self.num_earthlings + bonus

	def __getitem__(self, die_face):
		return self.__counts.get(die_face, 0)

	@property
	def num_earthlings(self):
		return sum(self[key] for key in EARTHLINGS)

	@property
	def collected_earthlings(self):
		return [key for key in EARTHLINGS if self[key] > 0]

	@property
	def total_collected(self):
		return sum(self.__counts.values())

	def add(self, die_face, number):
		new_counts = dict(self.__counts)
		new_counts[die_face] = new_counts.get(die_face, 0) + number
		return SideDiceState(new_counts)

	def update_tanks(self, num_tanks):
		return self.add(DieFace.Tank, num_tanks)

	def __str__(self):
		return str(self.__counts)

	def __getstate__(self):
		return dict((die.name, count) for die, count in self.__counts.items())

class DiceThrow:

	@staticmethod
	def random_throw(num_dice):
		counts = {}

		for die_throw in range(num_dice):
			die = randint(0, 5)
			if die > DieFace.Ray:
				die -= 1
			die_face = DieFace(die)
			counts[die_face] = counts.get(die_face, 0) + 1

		return DiceThrow(counts)

	def __init__(self, counts):
		self.__counts = counts

	@property
	def num_dice(self):
		return sum(self.__counts.values())

	def __getitem__(self, die_face):
		return self.__counts.get(die_face, 0)

	def remove(self, die_face):
		new_counts = dict(self.__counts)
		del new_counts[die_face]
		return DiceThrow(new_counts)

	def set_num(self, die_face, count):
		if count == 0:
			return self.remove(die_face)
		else:
			new_counts = dict(self.__counts)
			new_counts[die_face] = count
			return DiceThrow(new_counts)

	def __str__(self):
		return str(self.__counts)

	def __getstate__(self):
		return dict((die.name, count) for die, count in self.__counts.items())

def random_throw(state):
	return DiceThrow.random_throw(NUM_DICE - state.total_collected)

class TurnState:

	DEFAULT_CONFIG = { "throw_fun": random_throw }

	def __init__(
		self, throw = None, side_dice = None, phase = TurnPhase.Throwing, throw_count = 0
	):
		self.side_dice = side_dice or SideDiceState()
		self.phase = phase
		self.throw = throw
		self.throw_count = throw_count

	@property
	def score(self):
		return self.side_dice.score

	@property
	def done(self):
		return self.phase == TurnPhase.Done

	@property
	def awaitsInput(self):
		assert(not self.done)
		return self.phase == TurnPhase.PickDice or self.phase == TurnPhase.ThrowAgain

	@property
	def selectable_earthlings(self):
		return [key for key in EARTHLINGS if self.side_dice[key] == 0 and self.throw[key] > 0]

	def can_select(self, die):
		if die == DieFace.Ray:
			return self.throw[DieFace.Ray] > 0
		return die in self.selectable_earthlings

	def next(self, input_value = None, config = DEFAULT_CONFIG):
		assert(self.awaitsInput != (input_value is None))

		if self.phase == TurnPhase.Throwing:
			throw = config["throw_fun"](self.side_dice)
			return self._set_throw(throw)
		elif self.phase == TurnPhase.Thrown:
			return self._move_tanks()
		elif self.phase == TurnPhase.PickDice:
			return self._handle_pick(input_value)
		elif self.phase == TurnPhase.PostPick:
			return self._check_post_pick_exit()
		elif self.phase == TurnPhase.ThrowAgain:
			return self._check_player_exit(input_value)
		else:
			assert(False)

	def _end_turn(self, end_cause):
		new_state = TurnState(
			throw = None,
			throw_count = self.throw_count,
			side_dice = self.side_dice,
			phase = TurnPhase.Done
		)
		new_state.end_cause = end_cause

		return new_state

	def _set_throw(self, throw):
		assert(self.phase == TurnPhase.Throwing)

		new_state = TurnState(
			throw = throw,
			throw_count = self.throw_count + 1,
			side_dice = self.side_dice,
			phase = TurnPhase.Thrown
		)
		if throw[DieFace.Tank] == 0:
			new_state.skip_when_animating = True

		return new_state

	def _move_tanks(self):
		assert(self.phase == TurnPhase.Thrown)

		new_tanks = self.throw[DieFace.Tank]
		if new_tanks > 0:
			side_dice = self.side_dice.update_tanks(new_tanks)
			throw = self.throw.remove(DieFace.Tank)
		else:
			side_dice = self.side_dice
			throw = self.throw

		return TurnState(
			throw = throw,
			throw_count = self.throw_count,
			side_dice = side_dice,
			phase = TurnPhase.PickDice
		)._check_post_throw_exit()

	def _check_post_throw_exit(self):
		rays = self.throw[DieFace.Ray]
		selectable_earthlings = self.selectable_earthlings
		if rays > 0 or len(selectable_earthlings) == 0:
			forced_earthlings = 0
		else:
			forced_earthlings = min(self.throw[x] for x in selectable_earthlings)
		tanks = self.side_dice[DieFace.Tank]
		max_rays = NUM_DICE - tanks - self.side_dice.num_earthlings - forced_earthlings

		if tanks > max_rays:
			return self._end_turn("Defeated")
		elif len(selectable_earthlings) == 0 and rays == 0:
			if tanks > self.side_dice[DieFace.Ray]:
				return self._end_turn("Defeated")
			else:
				return self._end_turn("No selectable dice")

		return self

	def _handle_pick(self, selected_die):
		assert(self.phase == TurnPhase.PickDice)
		assert(self.throw[selected_die] > 0)
		assert(selected_die == DieFace.Ray or self.side_dice[selected_die] == 0)

		new_state = TurnState(
			throw = self.throw.remove(selected_die),
			throw_count = self.throw_count,
			side_dice = self.side_dice.add(selected_die, self.throw[selected_die]),
			phase = TurnPhase.PostPick
		)
		new_state.last_pick = selected_die

		return new_state

	def _check_post_pick_exit(self):
		assert(self.phase == TurnPhase.PostPick)

		if self.side_dice.total_collected == NUM_DICE:
			return self._end_turn("No more dice")

		if self.score > 0 and len(self.side_dice.collected_earthlings) == 3:
			return self._end_turn("Cannot improve score")

		return TurnState(
			throw = None,
			throw_count = self.throw_count,
			side_dice = self.side_dice,
			phase = TurnPhase.ThrowAgain if self.score > 0 else TurnPhase.Throwing
		)

	def _check_player_exit(self, stop):
		assert(self.phase == TurnPhase.ThrowAgain)

		if stop:
			return self._end_turn("Player choice")

		return TurnState(
			throw = None,
			throw_count = self.throw_count,
			side_dice = self.side_dice,
			phase = TurnPhase.Throwing
		)

	def __str__(self):
		return f"phase={self.phase.name}, side_dice={self.side_dice}"

	def __getstate__(self):
		state = {
			"throw_count": self.throw_count,
			"phase": self.phase.name,
			"side_dice": self.side_dice,
		}

		if self.throw:
			state["throw"] = self.throw
		if self.phase == TurnPhase.Done:
			state["score"] = self.score
			state["end_cause"] = self.end_cause

		return state

	def __str__(self):
		return str(self.__getstate__())
