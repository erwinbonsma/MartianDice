"""
State:
	T: Number of tanks
	D: Number of deathrays
	S: Total points collected sofar
	N: Total of point-groups selected (0 <= N <= 3)

Throw:
	T: Number of tanks
	D: Number of deathrays
	Q: Number of non-selectable point dice
		- Can be omitted?
	P[]: Number of points that can be selected
		- Ignores duplicates

Constraints:
	Len(State.P) + Len(Throw.P) <= 3

Actions:
	-1: No selection (bust or cannot select any dice)
	0: Select ray
	n: Select n earthlings
"""

from enum import IntEnum
from functools import reduce
from itertools import chain, combinations, groupby
from math import factorial
from collections import namedtuple
from game.DataTypes import *

SearchState = namedtuple('State', ['tanks', 'rays', 'earthlings', 'earthling_types'])
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

def update_state(state, throw, action):
	tanks = state.tanks + throw.tanks
	if action == 0:
		assert(throw.rays > 0)
		state = SearchState(
			tanks, state.rays + throw.rays, state.earthlings, state.earthling_types
		)
	elif action > 0:
		assert(action in throw.earthling_choices)
		state = SearchState(
			tanks, state.rays, state.earthlings + action, state.earthling_types + 1
		)
	else:
		state = SearchState(
			tanks, state.rays, state.earthlings, state.earthling_types
		)
	assert(state.earthling_types <= 3)
	assert(state.tanks + state.rays + state.earthlings <= NUM_DICE)
	return state

def score(state):
	if state.tanks > state.rays:
		return 0
	bonus = 3 if state.earthling_types == 3 else 0
	return state.earthlings + bonus

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
		earthlings = [0] * (3 - selected_earthling_types)
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

class OptimalActionSelector:

	def __init__(self):
		self.lookup = {}

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

	def expected_score(self, state, depth = 0, trace = False, check_throws = False):
		current_score = score(state)
		if state.earthling_types == 3 and current_score > 0:
			if trace:
				print("  " * depth, state, current_score, "Cannot improve score")
			return current_score
		rem_dice = NUM_DICE - state.tanks - state.rays - state.earthlings
		if rem_dice == 0:
			if trace:
				print("  " * depth, state, current_score, "No more dice")
			return current_score
		assert(rem_dice > 0)

		if state in self.lookup:
			if trace:
				print("  " * depth, state, self.lookup[state], "From lookup")
			return self.lookup[state]

		sum_score = 0
		num_outcomes = 0

		die_options = [(DieResult.Tank, 1), (DieResult.Ray, 1)]
		die_options.append((DieResult.SelectableEarthling, 3 - state.earthling_types))
		if state.earthling_types > 0:
			die_options.append((DieResult.UnselectableEarthling, 1))
		num_die_options = 5 - max(0, state.earthling_types - 1)

		if check_throws:
			counts1 = count_throws(rem_dice, state.earthling_types)
			print("Total:", sum(x for x in counts1.values()))
			counts2 = {}

		for group in groups_generator(rem_dice, max_num_groups = num_die_options):
			num_perms = num_permutations(group)

			for allocation in allocation_generator(classify_group(group), die_options):
				throw, multiplier = self.throw_for_allocation(state, group, allocation)
				assert(len(throw.earthling_choices) + state.earthling_types <= 3)
				_, expected_score = self.maximise_score(state, throw, depth + 1)
				if depth == 0 and trace:
					print(group, allocation, throw, expected_score, num_perms, multiplier, num_perms * multiplier)
				if check_throws:
					counts2[throw] = counts2.setdefault(throw, 0) + num_perms * multiplier
				sum_score += expected_score * num_perms * multiplier
				num_outcomes += num_perms * multiplier

		if check_throws:
			for key in counts1:
				if not key in counts2:
					print("Missing throw", key, counts1[key])
				elif counts1[key] != counts2[key]:
					print("Mismatch", key, counts1[key], counts2[key])

		assert(num_outcomes == 6**rem_dice)

		expected_score = sum_score / num_outcomes
		self.lookup[state] = expected_score if expected_score > current_score else current_score
		if trace:
			print("  " * depth, state, self.lookup[state], "Weighted score")
		return self.lookup[state]

	def bust(self, state, throw):
		tanks = state.tanks + throw.tanks
		forced_earthling = min(throw.earthling_choices) if throw.rays == 0 else 0
		return tanks > NUM_DICE - state.earthlings - forced_earthling - tanks

	def maximise_score(self, state, throw, depth = 0):
		possible_actions = actions_for_throw(throw)
		if len(possible_actions) == 0 or self.bust(state, throw):
			action = -1
			final_score = score(update_state(state, throw, action))
			return action, final_score

		evals = ((action, self.expected_score(update_state(
			state, throw, action
		), depth)) for action in possible_actions)

		return max(evals, key = lambda x: x[1])

	def select_die(self, state, throw):
		search_state = SearchState(
			state[DieFace.Tank]- throw[DieFace.Tank], state[DieFace.Ray],
			state.num_earthlings(), len(state.collected_earthlings())
		)
		search_throw = SearchThrow(
			throw[DieFace.Tank], throw[DieFace.Ray],
			tuple(set(throw[key] for key in EARTHLINGS if throw[key] > 0 and state[key] == 0))
		)

		action, self.__expected_score = self.maximise_score(search_state, search_throw)

		if action == 0:
			return DieFace.Ray

		for key in EARTHLINGS:
			if throw[key] == action and state[key] == 0:
				return key

	def should_stop(self, state):
		return state.score() == self.__expected_score

if __name__ == '__main__':
	import doctest
	doctest.testmod()

	action_selector = OptimalActionSelector()
	print("Expected average score:", action_selector.expected_score(SearchState(0, 0, 0, 0)))

	from game.Game import play_game
	num_games = 100000
	summed_scores = sum(play_game(action_selector, output = False) for _ in range(num_games))
	print("Avg score:", summed_scores / num_games)
