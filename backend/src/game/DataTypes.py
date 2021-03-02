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

	def update_tanks(self, num_tanks):
		self.add(DieFace.Tank, num_tanks)

	def score(self):
		if self[DieFace.Tank] > self[DieFace.Ray]:
			return 0
		bonus = 3 if sum(1 for key in EARTHLINGS if self[key] > 0) == 3 else 0
		return self.num_earthlings() + bonus

	def __str__(self):
		return str(self.__counts)

	def __getstate__(self):
		return dict((die.name, count) for die, count in self.__counts.items())

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

	def __getstate__(self):
		return dict((die.name, count) for die, count in self.__counts.items())

class TurnState:

	def __init__(self, throw_fun = None, start_side_state = None):
		self.throw_fun = throw_fun
		self.side_dice = start_side_state.copy() if start_side_state else SideDiceState()
		self.phase = TurnPhase.Throwing
		self.throw = None
		self.throw_count = 0

	@property
	def score(self):
		return self.side_dice.score()

	@property
	def done(self):
		return self.phase == TurnPhase.Done

	@property
	def awaitsInput(self):
		assert(not self.done)
		return self.phase == TurnPhase.PickDice or self.phase == TurnPhase.ThrowAgain

	def next(self, input_value = None):
		assert(self.awaitsInput != (input_value is None))

		if self.phase == TurnPhase.Throwing:
			self._set_throw(self.throw_fun(self.side_dice))
		elif self.phase == TurnPhase.Thrown:
			self._move_tanks()
		elif self.phase == TurnPhase.PickDice:
			self._handle_pick(input_value)
		elif self.phase == TurnPhase.PostPick:
			self._check_post_pick_exit()
		elif self.phase == TurnPhase.ThrowAgain:
			self._check_player_exit(input_value)
		else:
			assert(False)

	def selectable_earthlings(self):
		return [key for key in EARTHLINGS if self.side_dice[key] == 0 and self.throw[key] > 0]

	def can_select(self, die):
		if die == DieFace.Ray:
			return self.throw[DieFace.Ray] > 0
		return die in self.selectable_earthlings()

	def _set_throw(self, throw):
		assert(self.phase == TurnPhase.Throwing)

		self.throw = throw
		self.throw_count += 1
		self.phase = TurnPhase.Thrown

		rays = self.throw[DieFace.Ray]
		selectable_earthlings = self.selectable_earthlings()
		if rays > 0 or len(selectable_earthlings) == 0:
			forced_earthlings = 0
		else:
			forced_earthlings = min(self.throw[x] for x in selectable_earthlings)
		tanks = self.side_dice[DieFace.Tank] + self.throw[DieFace.Tank]
		max_rays = NUM_DICE - tanks - self.side_dice.num_earthlings() - forced_earthlings

		if tanks > max_rays:
			self.done_reason = "Defeated"
		elif len(selectable_earthlings) == 0 and rays == 0:
			if tanks > self.side_dice[DieFace.Ray]:
				self.done_reason = "Defeated"
			else:
				self.done_reason = "No selectable dice"
		else:
			self.done_reason = None

	def _move_tanks(self):
		assert(self.phase == TurnPhase.Thrown)

		new_tanks = self.throw[DieFace.Tank]
		if new_tanks > 0:
			self.side_dice.update_tanks(new_tanks)
			self.throw.set_num(DieFace.Tank, 0)

		self.phase = TurnPhase.Done if self.done_reason else TurnPhase.PickDice

	def _handle_pick(self, selected_die):
		assert(self.phase == TurnPhase.PickDice)
		assert(self.throw[selected_die] > 0)
		assert(selected_die == DieFace.Ray or self.side_dice[selected_die] == 0)

		self.side_dice.add(selected_die, self.throw[selected_die])
		self.throw.set_num(selected_die, 0)
		self.last_pick = selected_die
		self.phase = TurnPhase.PostPick

	def _check_post_pick_exit(self):
		assert(self.phase == TurnPhase.PostPick)

		self.throw = None

		if self.side_dice.total_collected() == NUM_DICE:
			self.phase = TurnPhase.Done
			self.done_reason = "No more dice"
			return

		if self.score > 0 and len(self.side_dice.collected_earthlings()) == 3:
			self.phase = TurnPhase.Done
			self.done_reason = "Cannot improve score"
			return

		self.phase = TurnPhase.ThrowAgain if self.score > 0 else TurnPhase.Throwing

	def _check_player_exit(self, stop):
		assert(self.phase == TurnPhase.ThrowAgain)

		if stop:
			self.phase = TurnPhase.Done
			self.done_reason = "Player choice"
			return

		self.phase = TurnPhase.Throwing

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
			state["end_cause"] = self.done_reason

		return state
