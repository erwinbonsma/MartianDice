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
	MovedTanks = 2
	PickDice = 3
	PickedDice = 4
	CheckPass = 5
	Done = 6

class Dice:

	def __init__(self, counts = {}):
		self._counts = counts

	@classmethod 
	def from_dict(cls, dict):
		self = cls.__new__(cls)
		self.__setstate__(dict)
		return self

	def to_dict(self):
		return self.__getstate__()

	def __getitem__(self, die_face):
		return self._counts.get(die_face, 0)

	@property
	def num_dice(self):
		return sum(self._counts.values())

	def __str__(self):
		return str(self._counts)

	def __getstate__(self):
		return dict((die.name, self._counts[die]) for die in sorted(self._counts.keys()))

	def __setstate__(self, state):
		self._counts = dict((DieFace[die_name], count) for die_name, count in state.items())

class SideDiceState(Dice):

	@property
	def score(self):
		if self[DieFace.Tank] > self[DieFace.Ray]:
			return 0
		bonus = 3 if sum(1 for key in EARTHLINGS if self[key] > 0) == 3 else 0
		return self.num_earthlings + bonus

	@property
	def num_earthlings(self):
		return sum(self[key] for key in EARTHLINGS)

	@property
	def collected_earthlings(self):
		return [key for key in EARTHLINGS if self[key] > 0]

	@property
	def total_collected(self):
		return self.num_dice

	def add(self, die_face, number):
		new_counts = dict(self._counts)
		new_counts[die_face] = new_counts.get(die_face, 0) + number
		return SideDiceState(new_counts)

	def update_tanks(self, num_tanks):
		return self.add(DieFace.Tank, num_tanks)

class DiceThrow(Dice):

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

	def remove(self, die_face):
		new_counts = dict(self._counts)
		del new_counts[die_face]
		return DiceThrow(new_counts)

	def set_num(self, die_face, count):
		if count == 0:
			return self.remove(die_face)
		else:
			new_counts = dict(self._counts)
			new_counts[die_face] = count
			return DiceThrow(new_counts)

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

	@classmethod 
	def from_dict(cls, dict):
		self = cls.__new__(cls)
		self.__setstate__(dict)
		return self

	def to_dict(self):
		return self.__getstate__()

	@property
	def score(self):
		return self.side_dice.score

	@property
	def done(self):
		return self.phase == TurnPhase.Done

	@property
	def awaits_input(self):
		assert(not self.done)
		return self.phase == TurnPhase.PickDice or self.phase == TurnPhase.CheckPass

	@property
	def selectable_earthlings(self):
		return [key for key in EARTHLINGS if self.side_dice[key] == 0 and self.throw[key] > 0]

	def can_select(self, die):
		if die == DieFace.Ray:
			return self.throw[DieFace.Ray] > 0
		return die in self.selectable_earthlings

	def next(self, input_value = None, config = DEFAULT_CONFIG):
		assert(self.awaits_input != (input_value is None))

		if input_value == "end-turn":
			return self._end_turn("Turn forcefully ended")
		if self.phase == TurnPhase.Throwing:
			throw = config["throw_fun"](self.side_dice)
			return self._set_throw(throw)
		if self.phase == TurnPhase.Thrown:
			return self._move_tanks()
		if self.phase == TurnPhase.MovedTanks:
			return self._check_post_throw_exit()
		if self.phase == TurnPhase.PickDice:
			return self._handle_pick(input_value)
		if self.phase == TurnPhase.PickedDice:
			return self._check_post_pick_exit()
		if self.phase == TurnPhase.CheckPass:
			return self._check_player_exit(input_value)

		assert(False)

	def _end_turn(self, end_cause, clear_throw = True):
		new_state = TurnState(
			throw = None if clear_throw else self.throw,
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

		new_state = TurnState(
			throw = throw,
			throw_count = self.throw_count,
			side_dice = side_dice,
			phase = TurnPhase.MovedTanks
		)

		if new_tanks == 0:
			new_state.skip_when_animating = True

		return new_state

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
			return self._end_turn("Defeated", clear_throw = False)
		elif len(selectable_earthlings) == 0 and rays == 0:
			if tanks > self.side_dice[DieFace.Ray]:
				return self._end_turn("Defeated", clear_throw = False)
			else:
				return self._end_turn("No selectable dice", clear_throw = False)

		return TurnState(
			throw = self.throw,
			throw_count = self.throw_count,
			side_dice = self.side_dice,
			phase = TurnPhase.PickDice
		)

	def _handle_pick(self, selected_die):
		assert(self.phase == TurnPhase.PickDice)
		assert(self.throw[selected_die] > 0)
		assert(selected_die == DieFace.Ray or self.side_dice[selected_die] == 0)

		new_state = TurnState(
			throw = self.throw.remove(selected_die),
			throw_count = self.throw_count,
			side_dice = self.side_dice.add(selected_die, self.throw[selected_die]),
			phase = TurnPhase.PickedDice
		)
		new_state.picked = selected_die

		return new_state

	def _check_post_pick_exit(self):
		assert(self.phase == TurnPhase.PickedDice)

		if self.side_dice.total_collected == NUM_DICE:
			return self._end_turn("No more dice")

		if self.score > 0 and len(self.side_dice.collected_earthlings) == 3:
			return self._end_turn("Cannot improve score")

		return TurnState(
			throw = None,
			throw_count = self.throw_count,
			side_dice = self.side_dice,
			phase = TurnPhase.CheckPass if self.score > 0 else TurnPhase.Throwing
		)

	def _check_player_exit(self, stop):
		assert(self.phase == TurnPhase.CheckPass)

		if stop:
			return self._end_turn("Player choice")

		return TurnState(
			throw = None,
			throw_count = self.throw_count,
			side_dice = self.side_dice,
			phase = TurnPhase.Throwing
		)

	def __getstate__(self):
		state = {
			"throw_count": self.throw_count,
			"phase": self.phase.name,
			"side_dice": self.side_dice.to_dict(),
		}

		if self.throw:
			state["throw"] = self.throw.to_dict()
		if self.phase == TurnPhase.Done:
			state["score"] = self.score
			state["end_cause"] = self.end_cause
		if self.phase == TurnPhase.PickedDice:
			state['picked'] = self.picked.name

		return state

	def __setstate__(self, state):
		state["phase"] = TurnPhase[state["phase"]]
		state["side_dice"] = SideDiceState.from_dict(state["side_dice"])
		if "throw" in state:
			state["throw"] = DiceThrow.from_dict(state["throw"])
		else:
			state["throw"] = None
		self.__dict__.update(state)

	def __str__(self):
		return str(self.__getstate__())
