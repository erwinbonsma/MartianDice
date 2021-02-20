from game.DataTypes import DieFace, RoundState
from game.Game import play_round
from game.OptimalPlay import OptimalActionSelector, SearchState
import unittest
import itertools

class TestOptimalActionSelector(unittest.TestCase):
	def setUp(self):
		self.action_selector = OptimalActionSelector()
	def tearDown(self):
		pass

	def testExpectedScoreOfOneDieThrow(self):
		state = SearchState(0, 10, 2, 1)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (2 * 3 + 4 * 2) / 6)

	def testExpectedScoreOfOneDieThrow2(self):
		state = SearchState(0, 10, 2, 2)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (1 * 6 + 5 * 2) / 6)

	def testExpectedScoreOfOneDieThrow3(self):
		state = SearchState(5, 5, 2, 1)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (2 * 3 + 3 * 2 + 1 * 0) / 6)

	def testExpectedScoreOfOneDieThrow4(self):
		state = SearchState(0, 9, 3, 2)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (1 * 7 + 5 * 3) / 6)

	def testExpectedScoreOfOneDieThrow5(self):
		state = SearchState(0, 10, 2, 1)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (2 * 3 + 4 * 2) / 6)

	def testExpectedScoreOfTwoDieThrow6(self):
		state = SearchState(0, 9, 2, 1)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (314 / 3) / 36)

	def testExpectedScoreOfTwoDieThrow7(self):
		state = SearchState(5, 6, 0, 0)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state, trace = False)

	def testExpectedScoreOfTwoDieThrow8(self):
		state = SearchState(0, 8, 3, 2)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state, trace = False)

	def testExpectedScoreOfFourDie(self):
		state = SearchState(5, 4, 0, 0)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state, trace = False)

	def testExpectedScoreOfFiveDie(self):
		state = SearchState(5, 0, 3, 2)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state, trace = False)

	def testExpectedScoreOfThreeDieThrow(self):
		state = SearchState(0, 8, 2, 1)
		expected_score = self.action_selector.expected_score(state)

		state = RoundState({DieFace.Ray: 8, DieFace.Cow: 2})
		num_runs = 100000
		scores = [
			(key, sum(1 for _ in iter))
			for key, iter in itertools.groupby(
				sorted(play_round(self.action_selector, state = state.copy(), output = False)
				for _ in range(num_runs))
			)
		]
		simulated_score = sum(score * count for score, count in scores) / num_runs
		print(scores, simulated_score, expected_score)
		self.assertAlmostEqual(expected_score, simulated_score, delta = 0.01)

	def testExpectedScoreOfThreeDieThrow2(self):
		state = SearchState(4, 4, 2, 1)
		expected_score = self.action_selector.expected_score(state)

		state = RoundState({ DieFace.Tank: 4, DieFace.Ray: 4, DieFace.Chicken: 2 })
		num_runs = 100000
		scores = [
			(key, sum(1 for _ in iter))
			for key, iter in itertools.groupby(
				sorted(play_round(self.action_selector, state = state.copy(), output = False)
				for _ in range(num_runs))
			)
		]
		simulated_score = sum(score * count for score, count in scores) / num_runs
		print(scores, simulated_score, expected_score)
		self.assertAlmostEqual(expected_score, simulated_score, delta = 0.01)

	def testSimulator(self):
		state = RoundState({ DieFace.Ray: 9, DieFace.Cow: 2})
		num_runs = 100000
		scores = [
			(key, sum(1 for _ in iter))
			for key, iter in itertools.groupby(
				sorted(play_round(self.action_selector, state = state.copy(), output = False)
				for _ in range(num_runs))
			)
		]
		print(scores)
		avg_score = sum(score * count for score, count in scores) / num_runs
		print(avg_score)
		self.assertAlmostEqual(avg_score, (314 / 3) / 36, delta = 0.01)

if __name__ == '__main__':
	unittest.main()

