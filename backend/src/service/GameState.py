from enum import IntEnum
import jsonpickle
import random
from game.DataTypes import TurnState

TARGET_SCORE = 25

class GamePhase(IntEnum):
	Recruiting = 0,
	Playing = 1,
	Done = 2

class GameState:

	def __init__(self):
		self.phase = GamePhase.Recruiting

	@property
	def active_player(self):
		assert(self.phase == GamePhase.Playing)
		return self.players[self.active_player_index]

	def start_game(self, players):
		assert(self.phase == GamePhase.Recruiting)

		self.round = 0
		self.players = list(players)
		random.shuffle(self.players)
		self.active_player_index = 0
		self.score = dict((id, 0) for id in self.players)
		self.phase = GamePhase.Playing
		self.turn_state = None

	def start_turn(self, turn_state):
		assert(self.turn_state is None)
		self.turn_state = turn_state

	def end_turn(self):
		assert(self.phase == GamePhase.Playing)

		self.score[self.active_player] += self.turn_state.score

	def next_turn(self):
		assert(self.phase == GamePhase.Playing)

		self.turn_state = None

		if self.score[self.active_player] >= TARGET_SCORE:
			self.phase = GamePhase.Done
			self.active_player_index = None
			return False

		self.active_player_index += 1
		if self.active_player_index == len(self.players):
			self.active_player_index = 0
			self.round += 1

		return True

	def __getstate__(self):
		state = {
			"type": "game-state",
			"players": self.players,
			"score": self.score,
			"round": self.round,
			"turn_state": self.turn_state,
			"done": self.phase == GamePhase.Done
		}
		if self.phase == GamePhase.Playing:
			state["active_player"] = self.active_player

		return state

	def as_json(self):
		return jsonpickle.encode(self, unpicklable = False)
