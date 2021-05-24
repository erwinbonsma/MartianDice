from game.DataTypes import DieFace, SideDiceState
from game.Game import play_turn
from game.OptimalPlay import OptimalActionSelector, SearchState
import unittest
import itertools

class OptimalPlaySimulationTests(unittest.TestCase):
	def setUp(self):
		self.action_selector = OptimalActionSelector()
	def tearDown(self):
		pass

	def testExpectedScoreOfThreeDieThrow(self):
		state = SearchState(0, 8, 2, 1, 0)
		expected_score = self.action_selector.expected_score(state)

		state = SideDiceState({DieFace.Ray: 8, DieFace.Cow: 2})
		num_runs = 100000
		scores = [
			(key, sum(1 for _ in iter))
			for key, iter in itertools.groupby(
				sorted(play_turn(self.action_selector, ini_side_dice = state)
				for _ in range(num_runs))
			)
		]
		simulated_score = sum(score * count for score, count in scores) / num_runs
		print(scores, simulated_score, expected_score)
		self.assertAlmostEqual(expected_score, simulated_score, delta = 0.01)

	def testExpectedScoreOfThreeDieThrow2(self):
		state = SearchState(4, 4, 2, 1, 0)
		expected_score = self.action_selector.expected_score(state)

		state = SideDiceState({ DieFace.Tank: 4, DieFace.Ray: 4, DieFace.Chicken: 2 })
		num_runs = 100000
		scores = [
			(key, sum(1 for _ in iter))
			for key, iter in itertools.groupby(
				sorted(play_turn(self.action_selector, ini_side_dice = state)
				for _ in range(num_runs))
			)
		]
		simulated_score = sum(score * count for score, count in scores) / num_runs
		print(scores, simulated_score, expected_score)
		self.assertAlmostEqual(expected_score, simulated_score, delta = 0.01)

	def testSimulator(self):
		state = SideDiceState({ DieFace.Ray: 9, DieFace.Cow: 2})
		num_runs = 100000
		scores = [
			(key, sum(1 for _ in iter))
			for key, iter in itertools.groupby(
				sorted(play_turn(self.action_selector, ini_side_dice = state)
				for _ in range(num_runs))
			)
		]
		print(scores)
		avg_score = sum(score * count for score, count in scores) / num_runs
		print(avg_score)
		self.assertAlmostEqual(avg_score, (314 / 3) / 36, delta = 0.01)

if __name__ == '__main__':
	unittest.main()

