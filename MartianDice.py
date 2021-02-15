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
	Bust: Cannot avoid zero score
	Done: Cannot select any new dice
	Deathray: Select deathray
	AddPoints(n): Select points
"""

from collections import namedtuple
from enum import IntEnum
from functools import reduce
from itertools import chain, combinations, groupby
from random import randint, random
from math import factorial

State = namedtuple('State', ['tanks', 'rays', 'earthlings', 'earthling_types'])
Throw = namedtuple('Throw', ['tanks', 'rays', 'earthling_choices'])

class ActionType(IntEnum):
	Bust = 1
	Done = 2
	Ray = 3
	Earthling = 4

class DieResult(IntEnum):
	Tank = 1
	Ray = 2
	SelectableEarthling = 3
	UnselectableEarthling = 4

class Action:
	@property
	def done(self):
		return self.type == ActionType.Bust or self.type == ActionType.Done

	@property
	def type(self):
		return self.__type

	def __init__(self, type):
		self.__type = type

	def __str__(self):
		return str(self.type)

class DiceAction(Action):

	@property
	def num_dice(self):
		return self.__num_dice

	def __init__(self, type, num_dice):
		Action.__init__(self, type)
		self.__num_dice = num_dice

	def __str__(self):
		return str(self.type) + "x" + str(self.num_dice)

BustAction = Action(ActionType.Bust)
DoneAction = Action(ActionType.Done)

NDICE = 13

def num_choices(throw):
	return len(throw.earthling_choices) + (1 if throw.rays > 0 else 0)

def action_for_choice(choice, throw):
	if choice < len(throw.earthling_choices):
		return DiceAction(ActionType.Earthling, throw.earthling_choices[choice])
	else:
		return DiceAction(ActionType.Ray, throw.rays)

class ActionSelector:

	def forced_action(self, state, throw):
		if num_choices(throw) == 0:
			return DoneAction if score(state) > 0 else BustAction

		tanks = state.tanks + throw.tanks
		forced_earthling = min(throw.earthling_choices) if throw.rays == 0 else 0

		if tanks > NDICE - state.earthlings - forced_earthling - tanks:
			return BustAction

	def select_action(self, state, throw):
		action = self.forced_action(state, throw)
		if action is not None:
			return action

		choice = randint(0, num_choices(throw))
		return action_for_choice(choice, throw)

	def stop(self, state):
		return score(state) > 0 and random() > 0.5

def generate_throw(state):
	num_dice = NDICE - state.tanks - state.rays - state.earthlings
	tanks = 0
	rays = 0
	earthling_choices = [0] * (3 - state.earthling_types)

	for die_throw in range(num_dice):
		die = randint(0, 5)
		if die < 1:
			tanks += 1
		elif die < 3:
			rays += 1
		elif die < 3 + len(earthling_choices):
			earthling_choices[die - 3] += 1

	return Throw(tanks, rays, list(set(x for x in earthling_choices if x > 0)))

def update_state(state, throw, action):
	tanks = state.tanks + throw.tanks
	if action.type == ActionType.Ray:
		assert(action.num_dice == throw.rays)
		state = State(
			tanks, state.rays + throw.rays, state.earthlings, state.earthling_types
		)
	elif action.type == ActionType.Earthling:
		assert(action.num_dice in throw.earthling_choices)
		state = State(
			tanks, state.rays, state.earthlings + action.num_dice, state.earthling_types + 1
		)
	else:
		state = State(
			tanks, state.rays, state.earthlings, state.earthling_types
		)
	assert(state.earthling_types <= 3)
	assert(state.tanks + state.rays + state.earthlings <= NDICE)
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

class OptimalActionSelector(ActionSelector):

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

		return Throw(tanks, rays, reduced_earthling_choices), multiplier

	def expected_score(self, state, depth = 0, trace = False, check_throws = False):
		current_score = score(state)
		if state.earthling_types == 3 and current_score > 0:
			if trace:
				print("  " * depth, state, current_score, "Cannot improve score")
			return current_score
		rem_dice = NDICE - state.tanks - state.rays - state.earthlings
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

	def maximise_score(self, state, throw, depth = 0):
		action = self.forced_action(state, throw)
		if action is not None:
			final_score = score(update_state(state, throw, action))
			return action, final_score

		evals = ((choice, self.expected_score(update_state(
			state, throw, action_for_choice(choice, throw)
		), depth)) for choice in range(num_choices(throw)))
		best_choice, expected_score = max(
			evals,
			key = lambda x: x[1]
		)
		return action_for_choice(best_choice, throw), expected_score

	def select_action(self, state, throw):
		action, self.__expected_score = self.maximise_score(state, throw)
		#print("Action:", action, ", Expected score:", self.__expected_score)
		return action

	def stop(self, state):
		return score(state) == self.__expected_score

def play_game(action_selector, state = State(0, 0, 0, 0), trace = False):
	while True:
		throw = generate_throw(state)
		if trace:
			print("Throw:", throw)

		action = action_selector.select_action(state, throw)
		if trace:
			print("Action:", action)

		state = update_state(state, throw, action)
		if trace:
			print("State:", state)

		if action.done:
			break

		if action_selector.stop(state):
			if trace:
				print("Stopping")
			break

	s = score(state)
	if trace:
		print("Score:", s)

	return s

if __name__ == '__main__':
	import doctest
	doctest.testmod()

	action_selector = OptimalActionSelector()
	print("Expected average score:", action_selector.expected_score(State(0, 0, 0, 0)))

	num_games = 1000000
	summed_scores = sum(play_game(action_selector) for _ in range(num_games))
	print("Avg score:", summed_scores / num_games)
