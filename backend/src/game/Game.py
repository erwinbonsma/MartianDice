from random import choice, random
from game.DataTypes import *

class RandomPlayer:

	def select_die(self, state: TurnState):
		options = state.selectable_earthlings()
		if state.throw[DieFace.Ray] > 0:
			options.append(DieFace.Ray)
		return choice(options)

	def should_stop(self, state: TurnState):
		return state.score > 0 and random() > 0.5

	def __str__(self):
		return "RandomPlayer"

class DefensivePlayer:

	def select_die(self, state: TurnState):
		if state.throw[DieFace.Ray] > 0 and state.side_dice[DieFace.Tank] > state.side_dice[DieFace.Ray]:
			return DieFace.Ray
		options = state.selectable_earthlings()
		return choice(options) if len(options) > 0 else DieFace.Ray

	def should_stop(self, state: TurnState):
		buffer = state.side_dice[DieFace.Ray] - state.side_dice[DieFace.Tank]
		return state.score > 0 and (buffer < 2 or len(state.side_dice.collected_earthlings()) == 3)

	def __str__(self):
		return "DefensivePlayer"

def random_throw(state):
	return DiceThrow(NUM_DICE - state.total_collected())

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
	if side_dice.num_earthlings() > 0:
		print("Abducted earthlings:", " ".join(die_string(key, side_dice[key]) for key in EARTHLINGS if side_dice[key] > 0))

def show_state(state: TurnState):
	if state.phase == TurnPhase.Thrown:
		show_throw(state.throw_count, state.throw)
		return
	
	if state.phase == TurnPhase.PickDice:
		return

	if state.phase == TurnPhase.PostPick:
		print("%s selected" % (state.last_pick.name))
		print()
		show_side_dice(state.side_dice)
		return

	if state.phase == TurnPhase.ThrowAgain:
		print("Score (sofar):", state.score)
		return

	if state.phase == TurnPhase.Done:
		print(state.done_reason)
		print("Score:", state.score)

def dev_null(state):
	pass

def play_turn(action_selector, throw_fun = random_throw, ini_side_dice = None, state_listener = None):
	if state_listener is None:
		state_listener = dev_null

	state = TurnState(start_side_state = ini_side_dice, throw_fun = throw_fun)
	state_listener(state)

	while not state.done:
		if state.awaitsInput:
			if state.phase == TurnPhase.PickDice:
				selected_die = action_selector.select_die(state)
				state.next(selected_die)
			elif state.phase == TurnPhase.ThrowAgain:
				should_stop = action_selector.should_stop(state)
				state.next(should_stop)
			else:
				assert(False)
		else:
			state.next()
		state_listener(state)

	return state.score

if __name__ == '__main__':
	action_selector = DefensivePlayer()

	play_turn(action_selector, state_listener = show_state)

	for player in [RandomPlayer(), DefensivePlayer()]:
		num_turns = 100
		summed_score = sum(play_turn(player) for _ in range(num_turns))
		print("Average score of %s" % (player), summed_score / num_turns)
