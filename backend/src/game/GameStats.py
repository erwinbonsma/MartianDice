import itertools
import logging
import numpy as np
from game.Game import play_game, AggressivePlayer, DefensivePlayer, RandomPlayer
from game.OptimalPlay import OptimalActionSelector

logger = logging.getLogger('game.GameStats')

def build_pvp_matrix(players, num_runs):
	n = len(players)
	wins = np.zeros((n, n))
	for run in range(num_runs):
		logger.info("Run %d", run)
		for p1, p2 in itertools.product(range(n), range(n)):
			p1_wins = play_game([players[p1], players[p2]]) == 0
			if p1_wins:
				wins[p1, p2] += 1
	wins /= num_runs 
	return wins

if __name__ == '__main__':
	logging.getLogger('game').setLevel(logging.INFO)
	logging.getLogger('game').addHandler(logging.StreamHandler())

	op1 = OptimalActionSelector(consider_win_score = False)
	op2 = OptimalActionSelector(consider_win_score = True)
	players = [RandomPlayer(), AggressivePlayer(), DefensivePlayer(), op1, op2]
	m = build_pvp_matrix(players, 1000)
	print(m)

	# Result from run with num_runs = 100000
	# [[0.52269 0.46619 0.14833 0.07076 0.06384]
	#  [0.57006 0.51936 0.26260 0.15804 0.15225]
	#  [0.88807 0.78197 0.55335 0.29518 0.27899]
	#  [0.95299 0.87960 0.79029 0.55612 0.54123]
	#  [0.95552 0.88500 0.80395 0.57171 0.55634]]