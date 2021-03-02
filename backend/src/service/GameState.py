from enum import IntEnum
import jsonpickle
import random
from game.DataTypes import TurnState, TurnPhase

TARGET_SCORE = 25

class GameState:

	def __init__(self, players):
		self.players = list(players)
		random.shuffle(self.players)

		self.round = 1
		self.active_player_index = 0
		self.scores = dict((id, 0) for id in self.players)
		self.turn_state = TurnState()

	@property
	def done(self):
		return self.turn_state is None

	@property
	def active_player(self):
		assert(not self.done)
		return self.players[self.active_player_index]

	@property
	def awaitsInput(self):
		assert(not self.done)
		return (not self.turn_state.done) and self.turn_state.awaitsInput

	def next(self, input = None):
		assert(not self.done)

		if not self.turn_state.done:
			self.turn_state = self.turn_state.next(input)
		else:
			self._end_turn()

	def _end_turn(self):
		assert(not self.done)
		assert(self.turn_state.done)

		self.scores[self.active_player] += self.turn_state.score
		if self.scores[self.active_player] >= TARGET_SCORE:
			self.turn_state = None
			self.active_player_index = None
			return

		self.active_player_index += 1
		if self.active_player_index == len(self.players):
			self.active_player_index = 0
			self.round += 1
		self.turn_state = TurnState()

	def __getstate__(self):
		state = {
			"players": self.players,
			"round": self.round,
			"scores": self.scores,
			"done": self.done
		}
		if not self.done:
			state["turn_state"] = self.turn_state
			state["active_player"] = self.active_player

		return state

	def as_json(self):
		return jsonpickle.encode(self, unpicklable = False)
