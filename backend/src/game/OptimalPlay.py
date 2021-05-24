"""
State:
	T: Number of tanks
	D: Number of deathrays
	S: Total points collected sofar
	N: Total of point-groups selected (0 <= N <= 3)
	M: Maximum score. When non-zero, the score is bounded by this limit. It is used to take into
	   account how many points are needed to win the game. In order to reduce the state space, it
	   is also bounded by the maximum score that is achievable from the current state.

Throw:
	T: Number of tanks
	D: Number of deathrays
	P[]: Number of points that can be selected
		- Ignores duplicates

Constraints:
	State.N + Len(Throw.P) <= 3

Actions:
	-1: No selection (bust or cannot select any dice)
	0: Select ray
	n: Select n earthlings
"""

from enum import IntEnum
from functools import reduce
from itertools import chain, combinations, groupby
import logging
from math import factorial
from collections import namedtuple
from game.DataTypes import *
from game.Game import AbstractPlayer

logger = logging.getLogger('game.OptimalPlay')

SearchState = namedtuple('State', ['tanks', 'rays', 'earthlings', 'earthling_types', 'max_score'])
SearchThrow = namedtuple('Throw', ['tanks', 'rays', 'earthling_choices'])

class DieResult(IntEnum):
	Tank = 1
	Ray = 2
	SelectableEarthling = 3
	UnselectableEarthling = 4

def actions_for_throw(throw):
	if throw.rays == 0:
		return throw.earthling_choices
	else:
		return list(throw.earthling_choices) + [0]

def max_score(num_combatants, num_earthlings, num_earthling_types):
	throw_size = NUM_DICE - num_combatants - num_earthlings
	bonus = ALL_EARTHLING_BONUS if throw_size + num_earthling_types >= NUM_EARTHLING_TYPES else 0
	max_extra_earthlings = throw_size if num_earthling_types < NUM_EARTHLING_TYPES else 0
	return num_earthlings + max_extra_earthlings + bonus

def update_max_score(state):
	return SearchState(
		state.tanks, state.rays, state.earthlings, state.earthling_types,
		min(
			state.max_score,
			max_score(state.tanks + state.rays, state.earthlings, state.earthling_types)
		)
	)

def update_state(state, throw, action):
	tanks = state.tanks + throw.tanks
	if action == 0:
		assert(throw.rays > 0)
		state = SearchState(
			tanks, state.rays + throw.rays, state.earthlings, state.earthling_types, state.max_score
		)
	elif action > 0:
		assert(action in throw.earthling_choices)
		state = SearchState(
			tanks, state.rays, state.earthlings + action, state.earthling_types + 1, state.max_score
		)
	else:
		state = SearchState(
			tanks, state.rays, state.earthlings, state.earthling_types, state.max_score
		)
	if state.max_score > 0:
		state = update_max_score(state)
	assert(state.earthling_types <= 3)
	assert(state.tanks + state.rays + state.earthlings <= NUM_DICE)
	return state

def score(state):
	if state.tanks > state.rays:
		return 0
	bonus = ALL_EARTHLING_BONUS if state.earthling_types == NUM_EARTHLING_TYPES else 0
	total = state.earthlings + bonus
	return (total if state.max_score == 0 else min(total, state.max_score))

def groups_generator(n, max_num_groups = None, max_size = None, l = []):
	if max_size is None:
		max_size = n
	if max_num_groups is None:
		max_num_groups = n
	if n == 0:
		yield l
		return
	for size in range(max(0, (n - 1) // max_num_groups) + 1, min(max_size, n) + 1):
		yield from groups_generator(n - size, max_num_groups - 1, size, l + [size])

def allocation_generator(group_counts, elems, allocation = []):
	"""
	>>> list("".join(a) for a in allocation_generator([2, 1], [('A', 1), ('B', 2), ('C', 3)]))
	['ABB', 'ABC', 'ACB', 'ACC', 'BBA', 'BBC', 'BCA', 'BCB', 'BCC', 'CCA', 'CCB', 'CCC']
	"""
	if len(group_counts) == 0:
		yield allocation
		return
	num_groups = group_counts[0]
	pickable_elems = chain.from_iterable(
		((elem, i) for i in range(min(num_groups, count))) for elem, count in elems
	)
	for picks in combinations(pickable_elems, num_groups):
		pick_index = 0
		rem_elems = []
		picked = []
		valid = True
		for elem, count in elems:
			num_picked = 0
			while pick_index < len(picks) and picks[pick_index][0] == elem:
				if picks[pick_index][1] != num_picked:
					valid = False
					break
				picked.append(elem)
				num_picked += 1
				pick_index += 1
			if num_picked < count:
				rem_elems.append((elem, count - num_picked))
		if valid:
			yield from allocation_generator(group_counts[1:], rem_elems, allocation + picked)

def product(a, b):
	return a * b

def classify_group(group):
	"""
	>>> classify_group('abbccccdd')
	[1, 2, 4, 2]
	"""
	return list(sum(1 for x in g) for _, g in groupby(group))

def num_permutations(group):
	return factorial(sum(group)) // reduce(product, (factorial(n) for n in group))

def num_allocations(group, num_elems):
	classified = classify_group(group)
	dups = reduce(product, (factorial(n) for n in classified))
	return factorial(num_elems) // (factorial(num_elems - len(group)) * dups)

def count_throws(num_dice, selected_earthling_types, throws = [], counts = None):
	"""
	Counts the occurencess of each possible throw for the given number of dice and number of
	selected earthling types. It can be used for debugging.
	"""
	if counts == None:
		counts = {}

	if num_dice == 0:
		tanks = 0
		rays = 0
		earthlings = [0] * (NUM_EARTHLING_TYPES - selected_earthling_types)
		for die in throws:
			if die == 0:
				tanks += 1
			elif die < 3:
				rays += 1
			elif die < 6 - selected_earthling_types:
				earthlings[die - 3] += 1
		throw = Throw(tanks, rays, tuple(set(x for x in earthlings if x > 0)))
		counts[throw] = counts.setdefault(throw, 0) + 1
		return

	for die in range(6):
		count_throws(num_dice - 1, selected_earthling_types, throws + [die], counts)

	return counts

class OptimalActionSelector(AbstractPlayer):

	def __init__(self, consider_win_score = False):
		self.lookup = {}
		self.consider_win_score = consider_win_score

	def state_from_side_dice(self, side_dice, win_score = 0):
		max_score = win_score if self.consider_win_score else 0

		state = SearchState(
			side_dice[DieFace.Tank],
			side_dice[DieFace.Ray],
			side_dice.num_earthlings,
			len(side_dice.collected_earthlings),
			max_score
		)

		return (state if max_score == 0 else update_max_score(state))

	def throw_for_allocation(self, state, group, allocation):
		assert(len(group) == len(allocation))
		multiplier = 1
		tanks = 0
		rays = 0
		earthling_choices = []

		for num, die in zip(group, allocation):
			if die == DieResult.Tank:
				tanks += num
			elif die == DieResult.Ray:
				multiplier *= 2**num
				rays += num
			elif die == DieResult.SelectableEarthling:
				earthling_choices.append(num)
			elif die == DieResult.UnselectableEarthling:
				multiplier *= state.earthling_types**num
			else:
				assert(False)

		reduced_earthling_choices = tuple(set(earthling_choices))
		if len(earthling_choices) > 0:
			if len(reduced_earthling_choices) > 1:
				multiplier *= factorial(len(earthling_choices))
				if len(reduced_earthling_choices) < len(earthling_choices):
					multiplier //= 2
			if len(earthling_choices) < 3 - state.earthling_types:
				multiplier *= (3 - state.earthling_types)

		return SearchThrow(tanks, rays, reduced_earthling_choices), multiplier

	def expected_score(self, state):
		current_score = score(state)
		if state.earthling_types == 3 and current_score > 0:
			return current_score
		rem_dice = NUM_DICE - state.tanks - state.rays - state.earthlings
		if rem_dice == 0:
			return current_score
		assert(rem_dice > 0)

		if state in self.lookup:
			return self.lookup[state]

		sum_score = 0
		num_outcomes = 0

		# die_option is tuple ("result type", "number of sub-types within result type")
		die_options = [(DieResult.Tank, 1), (DieResult.Ray, 1)]
		die_options.append((DieResult.SelectableEarthling, NUM_EARTHLING_TYPES - state.earthling_types))
		if state.earthling_types > 0:
			die_options.append((DieResult.UnselectableEarthling, 1))
		num_die_options = NUM_DIE_FACE_TYPES - max(0, state.earthling_types - 1)

		for group in groups_generator(rem_dice, max_num_groups = num_die_options):
			num_perms = num_permutations(group)

			for allocation in allocation_generator(classify_group(group), die_options):
				throw, multiplier = self.throw_for_allocation(state, group, allocation)
				assert(len(throw.earthling_choices) + state.earthling_types <= NUM_EARTHLING_TYPES)
				_, expected_score = self.maximise_score(state, throw)
				sum_score += expected_score * num_perms * multiplier
				num_outcomes += num_perms * multiplier

		assert(num_outcomes == 6**rem_dice)

		expected_score = sum_score / num_outcomes
		self.lookup[state] = expected_score if expected_score > current_score else current_score

		return self.lookup[state]

	def bust(self, state, throw):
		tanks = state.tanks + throw.tanks
		forced_earthling = min(throw.earthling_choices) if throw.rays == 0 else 0
		return tanks > NUM_DICE - state.earthlings - forced_earthling - tanks

	def maximise_score(self, state, throw):
		possible_actions = actions_for_throw(throw)
		if len(possible_actions) == 0 or self.bust(state, throw):
			action = -1
			final_score = score(update_state(state, throw, action))
			return action, final_score

		evals = ((action, self.expected_score(update_state(
			state, throw, action
		))) for action in possible_actions)

		return max(evals, key = lambda x: x[1])

	def select_die(self, state: TurnState, win_score = 0):
		search_state = self.state_from_side_dice(state.side_dice, win_score)
		search_throw = SearchThrow(
			state.throw[DieFace.Tank], state.throw[DieFace.Ray],
			tuple(set(state.throw[key] for key in state.selectable_earthlings))
		)

		lookup_size_ini = len(self.lookup)
		action, _ = self.maximise_score(search_state, search_throw)
		if len(self.lookup) != lookup_size_ini:
			logger.info("Lookup expanded from %d to %d", lookup_size_ini, len(self.lookup))

		if action == 0:
			return DieFace.Ray

		for key in EARTHLINGS:
			if state.throw[key] == action and state.side_dice[key] == 0:
				return key

	def should_stop(self, state: TurnState, win_score = 0):
		search_state = self.state_from_side_dice(state.side_dice, win_score)
		expected_score = self.expected_score(search_state)
		# Note: floating point inaccuracies should never be an issue due to nature of calculation.
		# When passing is the best option, the expected score is always an integer number.
		return state.score >= expected_score

def test_deviations(action_selector, num_turns = 100, max_win_score = 13):
	counts = [0] * (max_win_score + 1)
	def state_listener(state):
		global num_choices
		if state.phase == TurnPhase.PickDice:
			ref_choice = action_selector.select_die(state)
			counts[0] += 1
			for win_score in range(1, max_win_score + 1):
				win_choice = action_selector.select_die(state, win_score)
				if win_choice != ref_choice:
					counts[win_score] += 1
					print("Diff for %s @ %d: %s vs %s" % (str(state), win_score, ref_choice, win_choice))

	for _ in range(num_turns):
		play_turn(action_selector, state_listener = state_listener)
	print(counts)

if __name__ == '__main__':
	import doctest
	doctest.testmod()

	from game.Game import play_turn, play_game

	action_selector = OptimalActionSelector(consider_win_score = True)
	print("Expected average score:", action_selector.expected_score(SearchState(0, 0, 0, 0, 0)))
	print(len(action_selector.lookup))

	test_deviations(action_selector)

	num_turns = 100000
	summed_scores = sum(play_turn(action_selector) for _ in range(num_turns))
	print("Avg score:", summed_scores / num_turns)
