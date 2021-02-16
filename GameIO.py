from DataTypes import DieFace, EARTHLINGS
from Game import play_game

die_keys = {
	DieFace.Ray: "R",
	DieFace.Chicken: "C",
	DieFace.Cow: "M",
	DieFace.Human: "H"
}

class HumanPlayer:

	def show_options(self, options):
		items = []
		for option in options:
			items.append("[%s] %s" % (die_keys[option], option.name))

		print(" ".join(items))

	def select_die(self, state, throw):
		options = [key for key in EARTHLINGS if state.num(key) == 0 and throw.num(key) > 0]
		if throw.num(DieFace.Ray) > 0:
			options.append(DieFace.Ray)

		while True:
			self.show_options(options)
			key = input("Your choice : ").upper()
			print(key)
			for option in options:
				if die_keys.get(option) == key:
					return option

	def should_stop(self, state):
		while True:
			choice = input("Continue (Y/N)? : ").upper()
			if choice == "Y" or choice == "N":
				return choice == "N"

	def __str__(self):
		return "HumanPlayer"

if __name__ == '__main__':
	action_selector = HumanPlayer()

	play_game(action_selector)
