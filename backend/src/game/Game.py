from abc import ABCMeta, abstractmethod
from random import choice, random
from game.DataTypes import *

class AbstractPlayer(metaclass=ABCMeta):

	@abstractmethod
	def select_die(self, state: TurnState, win_score = 0) -> DieFace:
		"""
		Returns the (type of) die to select from the given throw. It must be a valid move.

		When win_score is non-zero, this is the number of points to win the game. A player can use
		this when making a choice, for example, switch to a less ambitious choice that is less
		risky
		"""
		pass

	@abstractmethod
	def should_stop(self, state: TurnState, win_score = 0) -> bool:
		"""
		Return true iff the player should stop their turn.
		"""
		pass

class RandomPlayer(AbstractPlayer):

	def select_die(self, state: TurnState, win_score = 0):
		options = state.selectable_earthlings
		if state.throw[DieFace.Ray] > 0:
			options.append(DieFace.Ray)
		return choice(options)

	def should_stop(self, state: TurnState, win_score = 0):
		return state.score > 0 and random() > 0.5

	def __str__(self):
		return "RandomPlayer"

class AggressivePlayer(AbstractPlayer):

	def select_die(self, state: TurnState, win_score = 0):
		"""
		Always select the maximum number of earthlings possible that does not lead to inevitable
		defeat.
		"""
		rays_shortage = state.side_dice[DieFace.Tank] - state.side_dice[DieFace.Ray]
		max_earthlings = state.throw.num_dice - rays_shortage

		options = [e for e in state.selectable_earthlings if state.throw[e] <= max_earthlings]
		if len(options) == 0:
			return DieFace.Ray

		max_size = max(state.throw[e] for e in options)
		return choice([e for e in options if state.throw[e] == max_size])

	def should_stop(self, state: TurnState, win_score = 0):
		"""Only stop when no more move is possible"""
		return False

	def __str__(self):
		return "AggressivePlayer"

class DefensivePlayer(AbstractPlayer):

	def select_die(self, state: TurnState, win_score = 0):
		"""
		Always select a ray when there are more tanks than rays. Otherwise, collect the most earthlings.
		"""
		if state.throw[DieFace.Ray] > 0 and state.side_dice[DieFace.Tank] > state.side_dice[DieFace.Ray]:
			return DieFace.Ray
		options = state.selectable_earthlings
		if len(options) == 0:
			return DieFace.Ray
		max_size = max(state.throw[earthling] for earthling in options)
		return choice([earthling for earthling in options if state.throw[earthling] == max_size])

	def should_stop(self, state: TurnState, win_score = 0):
		buffer = state.side_dice[DieFace.Ray] - state.side_dice[DieFace.Tank]
		return state.score > 0 and (
			# Stop if doing so would win the game
			(win_score > 0 and state.score >= win_score) or
			# Or if a throw is considered too risky, given the battle state
			# TODO: Also take into account the number of dice to be thrown
			buffer < 2
		)

	def __str__(self):
		return "DefensivePlayer"

def die_string(die_face, number):
	return "%d %s%s" % (number, die_face.name, "s" if number > 1 else "")

def show_throw(throw_count, throw):
	items = []
	for name, member in DieFace.__members__.items():
		count = throw[member]
		if count > 0:
			items.append(die_string(member, count))

	print(f"Throw #{throw_count}:", ", ".join(items))

def show_side_dice(side_dice):
	print("%d deathrays vs %d tanks" % (side_dice[DieFace.Ray], side_dice[DieFace.Tank]))
	if side_dice.num_earthlings > 0:
		print("Abducted earthlings:", " ".join(die_string(key, side_dice[key]) for key in EARTHLINGS if side_dice[key] > 0))

def show_state(state: TurnState):
	if state.phase == TurnPhase.Thrown:
		show_throw(state.throw_count, state.throw)
		return
	
	if state.phase == TurnPhase.PickDice:
		return

	if state.phase == TurnPhase.PickedDice:
		print("%s selected" % (state.picked.name))
		print()
		show_side_dice(state.side_dice)
		return

	if state.phase == TurnPhase.CheckPass:
		print("Score (sofar):", state.score)
		return

	if state.phase == TurnPhase.Done:
		print(state.end_cause)
		print("Score:", state.score)

def dev_null(state):
	pass

def play_turn(
	action_selector,
	win_score = 0,
	throw_fun = random_throw, ini_side_dice = None,
	state_listener = None
):
	if state_listener is None:
		state_listener = dev_null

	state = TurnState(side_dice = ini_side_dice)
	state_listener(state)

	turn_config = { "throw_fun": throw_fun }

	while not state.done:
		if state.awaits_input:
			if state.phase == TurnPhase.PickDice:
				selected_die = action_selector.select_die(state, win_score)
				state = state.next(selected_die)
			elif state.phase == TurnPhase.CheckPass:
				should_stop = action_selector.should_stop(state, win_score)
				state = state.next(should_stop)
			else:
				assert(False)
		else:
			state = state.next(config = turn_config)
		state_listener(state)

	return state.score

def play_game(players, target_score = TARGET_SCORE):
	scores = [0] * len(players)
	turn = 0
	while True:
		player_index = turn % len(players)
		win_score = target_score - scores[player_index]
		scores[player_index] += play_turn(players[player_index], win_score)
		if scores[player_index] >= target_score:
			return player_index
		turn += 1

if __name__ == '__main__':
	action_selector = DefensivePlayer()

	play_turn(action_selector, state_listener = show_state)

	for player in [RandomPlayer(), DefensivePlayer(), AggressivePlayer()]:
		num_turns = 1000
		summed_score = sum(play_turn(player) for _ in range(num_turns))
		print("Average score of %s" % (player), summed_score / num_turns)
