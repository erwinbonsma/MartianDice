from enum import IntEnum
import jsonpickle
import random
import time
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
		self.from_hash = None
		self.winner = None
		self.last_update = time.time()

	@property
	def done(self):
		return self.turn_state is None

	@property
	def active_player(self):
		assert(not self.done)
		return self.players[self.active_player_index]

	@property
	def awaits_input(self):
		assert(not self.done)
		return (not self.turn_state.done) and self.turn_state.awaits_input

	@property
	def age_in_seconds(self):
		return time.time() - self.last_update

	def set_from_hash(self, from_hash):
		self.from_hash = from_hash

	def next(self, input = None):
		assert(not self.done)

		if not self.turn_state.done:
			self.turn_state = self.turn_state.next(input)
		else:
			self._end_turn()
		self.last_update = time.time()

	def _end_turn(self):
		assert(not self.done)
		assert(self.turn_state.done)

		self.scores[self.active_player] += self.turn_state.score
		if self.scores[self.active_player] >= TARGET_SCORE:
			self.winner = self.active_player
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
			"last_update": int(self.last_update)
		}
		if not self.done:
			state["turn_state"] = self.turn_state
			state["active_player"] = self.active_player
		if self.from_hash:
			state["from_hash"] = self.from_hash
		if self.winner:
			state["winner"] = self.winner

		return state

	def __setstate__(self, state):
		# Set defaults for optional variables
		self.from_hash = None
		self.winner = None
		self.turn_state = None

		active_player = state.get("active_player", None)
		if active_player:
			state["active_player_index"] = state["players"].index(active_player)
			del state["active_player"]
		self.__dict__.update(state)

	def __str__(self):
		return str(self.__getstate__())

	def as_json(self):
		return jsonpickle.encode(self, unpicklable = False)
