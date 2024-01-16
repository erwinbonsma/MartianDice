from game.DataTypes import random_throw
from game.GameIO import enter_throw, HumanPlayer
from game.Game import play_turn, show_state

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Play Martian Dice game.')
	parser.add_argument('--enter-throws', action='store_true', help='Manually enter dice throws')
	parser.add_argument('--show-hints', action='store_true', help='Recommend action based on expected score')
	args = parser.parse_args()

	action_selector = HumanPlayer(show_hint = args.show_hints)

	throw_fun = enter_throw if args.enter_throws else random_throw
	play_turn(action_selector, throw_fun = throw_fun, state_listener = show_state)
