from DataTypes import DiceThrow, DieFace, EARTHLINGS, NUM_DICE
from Game import play_game, show_throw
from OptimalPlay import OptimalActionSelector, SearchState

die2key = {
	DieFace.Tank: "T",
	DieFace.Ray: "R",
	DieFace.Chicken: "C",
	DieFace.Cow: "M",
	DieFace.Human: "H"
}

key2die = { key: die for die, key in die2key.items() }

def enter_throw(state):
	target_num_dice = NUM_DICE - state.total_collected()
	throw = DiceThrow()

	while throw.num_dice() != target_num_dice:
		if throw.num_dice() > 0:
			show_throw(throw)
		
		try:
			s = input("Add dice to throw (%d/%d): " % (throw.num_dice(), target_num_dice)).upper()
			if len(s) < 2:
				raise ValueError("Input too short")
			if not s[-1] in key2die:
				raise ValueError("Unknown die result")

			num = int(s[0:-1])
			throw.set_num(key2die[s[-1]], num)
		except ValueError:
			print("Enter number followed by die result (T, R, C, M, or H). E.g. '3T' for three Tanks")

	print()
	return throw

class HumanPlayer:

	def __init__(self, show_hint = False):
		self.hint_generator = OptimalActionSelector() if show_hint else None

	def show_options(self, options):
		items = []
		for option in options:
			items.append("[%s] %s" % (die2key[option], option.name))

		print(" ".join(items))

	def show_hint(self, state, throw):
		num_earthling_types = len(state.collected_earthlings())		
		scores = [
			(self.hint_generator.expected_score(
				SearchState(
					state.num(DieFace.Tank), state.num(DieFace.Ray),
					state.num_earthlings() + action, num_earthling_types + 1
				)
			), action)
			for action in list(set(throw.num(x) for x in state.selectable_earthlings(throw)))
		]
		if throw.num(DieFace.Ray) > 0:
			scores.append((
				self.hint_generator.expected_score(
					SearchState(
						state.num(DieFace.Tank), state.num(DieFace.Ray) + throw.num(DieFace.Ray),
						state.num_earthlings(), num_earthling_types
					)
				), 0
			))

		for score, action in sorted(scores, key = lambda x: x[0], reverse = True):
			if action > 0:
				choice = "%d Earthling%s" % (action, "s" if action > 1 else "")
			else:
				choice = "%d Ray%s" % (throw.num(DieFace.Ray), "s" if throw.num(DieFace.Ray) > 1 else "")
			print("%.3f %s" % (score, choice))

	def select_die(self, state, throw):
		options = [key for key in EARTHLINGS if state.num(key) == 0 and throw.num(key) > 0]
		if throw.num(DieFace.Ray) > 0:
			options.append(DieFace.Ray)

		if self.hint_generator is not None:
			self.show_hint(state, throw)

		while True:
			self.show_options(options)
			key = input("Your choice : ").upper()
			if key in key2die:
				return key2die[key]

	def should_stop(self, state):
		while True:
			choice = input("Continue (Y/N)? : ").upper()
			if choice == "Y" or choice == "N":
				return choice == "N"

	def __str__(self):
		return "HumanPlayer"

if __name__ == '__main__':
	action_selector = HumanPlayer(show_hint = True)

	play_game(action_selector)
