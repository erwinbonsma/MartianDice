from game.DataTypes import DieFace, SideDiceState, TurnState
from game.OptimalPlay import OptimalActionSelector, SearchState
import unittest

class OptimalPlayUnitTests(unittest.TestCase):
	def setUp(self):
		self.action_selector = OptimalActionSelector(consider_win_score = True)
	def tearDown(self):
		pass

	def testExpectedScoreOfOneDieThrow(self):
		state = SearchState(0, 10, 2, 1, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (2 * 3 + 4 * 2) / 6)

	def testExpectedScoreOfOneDieThrow2(self):
		state = SearchState(0, 10, 2, 2, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (1 * 6 + 5 * 2) / 6)

	def testExpectedScoreOfOneDieThrow3(self):
		state = SearchState(5, 5, 2, 1, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (2 * 3 + 3 * 2 + 1 * 0) / 6)

	def testExpectedScoreOfOneDieThrow4(self):
		state = SearchState(0, 9, 3, 2, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (1 * 7 + 5 * 3) / 6)

	def testExpectedScoreOfOneDieThrow5(self):
		state = SearchState(0, 10, 2, 1, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (2 * 3 + 4 * 2) / 6)

	def testExpectedScoreOfTwoDieThrow1(self):
		state = SearchState(0, 9, 2, 1, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (314 / 3) / 36)

	def testExpectedScoreOfTwoDieThrow2(self):
		state = SearchState(3, 3, 5, 2, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, (10 * 1 + 9 * 8 + 5 * 12 + (5 + 2/3) * 8 + 0 * 7) / 36)

	def testExpectedScoreOfTwoDieThrow3(self):
		# Similar to previous, but in this case, best move is to pass
		state = SearchState(2, 2, 7, 2, 0)
		expected_score = self.action_selector.expected_score(state)
		self.assertAlmostEqual(expected_score, 7)

	def testExpectedScoreOfTwoDieThrow_NoAsserts1(self):
		state = SearchState(5, 6, 0, 0, 0)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state)

	def testExpectedScoreOfTwoDieThrow_NoAsserts2(self):
		state = SearchState(0, 8, 3, 2, 0)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state)

	def testExpectedScoreOfFourDie(self):
		state = SearchState(5, 4, 0, 0, 0)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state)

	def testExpectedScoreOfFiveDie(self):
		state = SearchState(5, 0, 3, 2, 0)
		# Should not fail any assert built-in asserts
		expected_score = self.action_selector.expected_score(state)

	def testShouldStopWhenWinningEvenWhenOddsAreGood(self):
		state = TurnState(side_dice = SideDiceState({
			DieFace.Ray: 5, DieFace.Cow: 2
		}))

		self.assertTrue(self.action_selector.should_stop(state, 1))
		self.assertTrue(self.action_selector.should_stop(state, 2))
		self.assertFalse(self.action_selector.should_stop(state, 3))
		self.assertFalse(self.action_selector.should_stop(state))

if __name__ == '__main__':
	unittest.main()

