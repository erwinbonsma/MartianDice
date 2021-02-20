from random import choice, random
from game.DataTypes import *

class RandomPlayer:

	def select_die(self, state, throw):
		options = state.selectable_earthlings(throw)
		if throw[DieFace.Ray] > 0:
			options.append(DieFace.Ray)
		return choice(options)

	def should_stop(self, state):
		return state.score() > 0 and random() > 0.5

	def __str__(self):
		return "RandomPlayer"

class DefensivePlayer:

	def select_die(self, state, throw):
		if throw[DieFace.Ray] > 0 and state[DieFace.Tank] > state[DieFace.Ray]:
			return DieFace.Ray
		options = state.selectable_earthlings(throw)
		return choice(options) if len(options) > 0 else DieFace.Ray

	def should_stop(self, state):
		buffer = state[DieFace.Ray] - state[DieFace.Tank]
		return state.score() > 0 and (buffer < 2 or len(state.collected_earthlings()) == 3)

	def __str__(self):
		return "DefensivePlayer"

def random_throw(state):
	return DiceThrow(NUM_DICE - state.total_collected())

def die_string(die_face, number):
	return "%d %s%s" % (number, die_face.name, "s" if number > 1 else "")

def show_throw(throw):
	items = []
	for name, member in DieFace.__members__.items():
		count = throw[member]
		if count > 0:
			items.append(die_string(member, count))

	print("Throw:", ", ".join(items))

def show_state(state):
	print("%d deathrays vs %d tanks" % (state[DieFace.Ray], state[DieFace.Tank]))
	if state.num_earthlings() > 0:
		print("Abducted earthlings:", " ".join(die_string(key, state[key]) for key in EARTHLINGS if state[key] > 0))

def play_round(action_selector, throw_fun = random_throw, state = None, output = True):
	if state == None:
		state = RoundState()

	while True:
		throw = throw_fun(state)
		if output: show_throw(throw)

		state.update_tanks(throw)
		if state.is_done(throw):
			if output: print("Done!" if state.score() > 0 else "Bust!")
			break

		selected_die = action_selector.select_die(state, throw)
		if output:
			print("%s selected" % (selected_die.name))
			print()

		state.handle_choice(throw, selected_die)
		if output: show_state(state)

		if state.total_collected() == NUM_DICE or (
			state.score() > 0 and len(state.collected_earthlings()) == 3
		):
			break

		if state.score() > 0:
			if output: print("Score (sofar):", state.score())
			if action_selector.should_stop(state):
				break

		if output: print()

	score = state.score()
	if output:
		print("Score:", score)

	return score

if __name__ == '__main__':
	action_selector = DefensivePlayer()

	play_round(action_selector)

	for player in [RandomPlayer(), DefensivePlayer()]:
		num_games = 100
		summed_score = sum(play_round(player, output = False) for _ in range(num_games))
		print("Average score of %s" % (player), summed_score / num_games)
