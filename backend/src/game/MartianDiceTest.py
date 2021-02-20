from MartianDice import OptimalActionSelector, State, play_game, generate_throw
import unittest
import itertools

class TestOptimalActionSelector(unittest.TestCase):
    def setUp(self):
        self.action_selector = OptimalActionSelector()
    def tearDown(self):
        pass

    def testExpectedScoreOfOneDieThrow(self):
        state = State(0, 10, 2, 1)
        expected_score = self.action_selector.expected_score(state)
        self.assertAlmostEqual(expected_score, (2 * 3 + 4 * 2) / 6)

    def testExpectedScoreOfOneDieThrow2(self):
        state = State(0, 10, 2, 2)
        expected_score = self.action_selector.expected_score(state)
        self.assertAlmostEqual(expected_score, (1 * 6 + 5 * 2) / 6)

    def testExpectedScoreOfOneDieThrow3(self):
        state = State(5, 5, 2, 1)
        expected_score = self.action_selector.expected_score(state)
        self.assertAlmostEqual(expected_score, (2 * 3 + 3 * 2 + 1 * 0) / 6)

    def testExpectedScoreOfOneDieThrow4(self):
        state = State(0, 9, 3, 2)
        expected_score = self.action_selector.expected_score(state)
        self.assertAlmostEqual(expected_score, (1 * 7 + 5 * 3) / 6)

    def testExpectedScoreOfOneDieThrow5(self):
        state = State(0, 10, 2, 1)
        expected_score = self.action_selector.expected_score(state)
        self.assertAlmostEqual(expected_score, (2 * 3 + 4 * 2) / 6)

    def testExpectedScoreOfTwoDieThrow6(self):
        state = State(0, 9, 2, 1)
        expected_score = self.action_selector.expected_score(state)
        self.assertAlmostEqual(expected_score, (314 / 3) / 36)

    def testExpectedScoreOfTwoDieThrow7(self):
        state = State(5, 6, 0, 0)
        # Should not fail any assert built-in asserts
        expected_score = self.action_selector.expected_score(state, trace = False)

    def testExpectedScoreOfTwoDieThrow8(self):
        state = State(0, 8, 3, 2)
        # Should not fail any assert built-in asserts
        expected_score = self.action_selector.expected_score(state, trace = False)

    def testExpectedScoreOfFourDie(self):
        state = State(5, 4, 0, 0)
        # Should not fail any assert built-in asserts
        expected_score = self.action_selector.expected_score(state, trace = False)

    def testExpectedScoreOfFiveDie(self):
        state = State(5, 0, 3, 2)
        # Should not fail any assert built-in asserts
        expected_score = self.action_selector.expected_score(state, trace = False)

    def testExpectedScoreOfThreeDieThrow(self):
        state = State(0, 8, 2, 1)
        expected_score = self.action_selector.expected_score(state)
        num_runs = 100000
        scores = [
            (key, sum(1 for _ in iter))
            for key, iter in itertools.groupby(
                sorted(play_game(self.action_selector, state) for _ in range(num_runs))
            )
        ]
        simulated_score = sum(score * count for score, count in scores) / num_runs
        print(scores, simulated_score, expected_score)
        self.assertAlmostEqual(expected_score, simulated_score, delta = 0.01)

    def testExpectedScoreOfThreeDieThrow2(self):
        state = State(4, 4, 2, 1)
        expected_score = self.action_selector.expected_score(state)
        num_runs = 100000
        scores = [
            (key, sum(1 for _ in iter))
            for key, iter in itertools.groupby(
                sorted(play_game(self.action_selector, state) for _ in range(num_runs))
            )
        ]
        simulated_score = sum(score * count for score, count in scores) / num_runs
        print(scores, simulated_score, expected_score)
        self.assertAlmostEqual(expected_score, simulated_score, delta = 0.01)

    def testSimulator(self):
        state = State(0, 9, 2, 1)
        num_runs = 100000
        scores = [
            (key, sum(1 for _ in iter))
            for key, iter in itertools.groupby(
                sorted(play_game(self.action_selector, state) for _ in range(num_runs))
            )
        ]
        print(scores)
        avg_score = sum(score * count for score, count in scores) / num_runs
        print(avg_score)
        self.assertAlmostEqual(avg_score, (314 / 3) / 36, delta = 0.01)

    # def testThrows(self):
    #     state = State(0, 9, 2, 1)
    #     throws = [
    #         (key, sum(1 for _ in iter))
    #         for key, iter in itertools.groupby(
    #             sorted(generate_throw(state) for _ in range(100000))
    #         )
    #     ]
    #     print(throws)

if __name__ == '__main__':
    unittest.main()

