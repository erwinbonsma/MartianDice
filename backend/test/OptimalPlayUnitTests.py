from game.DataTypes import DiceThrow, DieFace, SideDiceState, TurnState
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

	def testDieChoiceDependsOnWinScore1(self):
		# State with four different choices depending on win score
		state = TurnState(
			side_dice = SideDiceState({ DieFace.Tank: 2 }),
			throw = DiceThrow({
				DieFace.Ray: 2, DieFace.Cow: 2, DieFace.Human: 3, DieFace.Chicken: 4
			})
		)

		self.assertEqual(DieFace.Chicken, self.action_selector.select_die(state))
		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state, 1))
		self.assertEqual(DieFace.Cow, self.action_selector.select_die(state, 2))
		self.assertEqual(DieFace.Human, self.action_selector.select_die(state, 3))

	def testDieChoiceDependsOnWinScore2(self):
		# State where choice deviates only for a couple of higher win scores.
		# It is more typical that there is a deviation for lower win scores up until a limit.
		state = TurnState(
			side_dice = SideDiceState({ DieFace.Tank: 1 }),
			throw = DiceThrow({
				DieFace.Ray: 4, DieFace.Cow: 1, DieFace.Human: 3, DieFace.Chicken: 4
			})
		)

		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state))
		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state, 3))

		self.assertEqual(DieFace.Chicken, self.action_selector.select_die(state, 4))
		self.assertEqual(DieFace.Chicken, self.action_selector.select_die(state, 5))

		score_ray0 = self.action_selector.expected_score(SearchState(1, 4, 0, 0, 0))
		score_ray4 = self.action_selector.expected_score(SearchState(1, 4, 0, 0, 4))
		score_kip0 = self.action_selector.expected_score(SearchState(1, 0, 4, 1, 0))
		score_kip4 = self.action_selector.expected_score(SearchState(1, 0, 4, 1, 4))

		self.assertGreater(score_ray0, score_kip0)
		self.assertGreater(score_kip4, score_ray4)
		self.assertGreaterEqual(score_ray0, score_ray4)
		self.assertGreaterEqual(score_kip0, score_kip4)

	def testDieChoiceDependsOnWinScore3(self):
		# State where choice deviates for low and high, but not medium scores
		state = TurnState(
			side_dice = SideDiceState({ DieFace.Tank: 1 }),
			throw = DiceThrow({
				DieFace.Ray: 5, DieFace.Cow: 1, DieFace.Human: 2, DieFace.Chicken: 4
			})
		)

		self.assertEqual(DieFace.Chicken, self.action_selector.select_die(state))
		self.assertEqual(DieFace.Chicken, self.action_selector.select_die(state, 4))
		self.assertEqual(DieFace.Chicken, self.action_selector.select_die(state, 5))
		self.assertEqual(DieFace.Chicken, self.action_selector.select_die(state, 6))

		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state, 1))
		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state, 2))
		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state, 3))
		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state, 7))
		self.assertEqual(DieFace.Ray, self.action_selector.select_die(state, 8))

if __name__ == '__main__':
	unittest.main()
