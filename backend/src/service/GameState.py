import hashlib
import json
import random
import time
from game.DataTypes import TurnState, TARGET_SCORE

class ChecksumMismatchException(Exception):
	def __init__(self, message):
		self.message = message

def game_state_id(game_state):
	if "id" in game_state:
		# game_state already contains "id", so apparently this is an integrity check. Remove "id"
		# so that the state equals that which was used to originally set the id.
		game_state = dict(game_state)
		del game_state["id"]

	s = json.dumps(game_state)
	return hashlib.md5(s.encode('utf-8')).hexdigest()[:8]

class GameState:

	def __init__(self, players):
		self.players = list(players)
		random.shuffle(self.players)

		self.round = 1
		self.active_player_index = 0
		self._init_turn_state()
		self.scores = {id: 0 for id in self.players}
		self.winner = None
		self.last_update = time.time()
		self.prev_id = None
		self.id = None
		self.num_updates = 0

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

	@property
	def num_players(self):
		return len(self.scores)

	def has_player(self, id):
		return id in self.scores

	def next(self, input = None):
		assert(not self.done)

		if self.id:
			self.prev_id = self.id
			self.id = None

		if not self.turn_state.done:
			self.turn_state = self.turn_state.next(input)
		else:
			self._end_turn()

		self.num_updates += 1
		self.last_update = time.time()

	def remove_player(self):
		del self.scores[self.active_player]
		self.players[self.active_player_index] = ""

	def _init_turn_state(self):
		self.turn_state = TurnState()
		# In first turn for new player, include metadata. This lets
		# clients that replay old turn transitions to signals changes
		# of player and rounds before they reach the latest game
		# state (typically one that requires input from a player)
		self.turn_state.metadata.update({
			"active_player": self.active_player,
			"round": self.round
		})

	def _next_turn(self):
		start_index = self.active_player_index

		while True:
			self.active_player_index += 1
			if self.active_player_index == len(self.players):
				self.active_player_index = 0
				self.round += 1

			# Skip players that have been removed from the game
			if self.active_player != "":
				break

			# Guard against endless loop
			assert(self.active_player_index != start_index)

		self._init_turn_state()

	def _active_player_wins(self):
		self.winner = self.active_player
		self.turn_state = None
		self.active_player_index = None

	def _end_turn(self):
		assert(not self.done)
		assert(self.turn_state.done)

		if self.active_player != "":
			# Only update score when player was not just removed
			self.scores[self.active_player] += self.turn_state.score
			self.turn_state.metadata["total_score"] = self.scores[self.active_player]
			if self.scores[self.active_player] >= TARGET_SCORE:
				return self._active_player_wins()

		self._next_turn()

		if len(self.scores) == 1:
			# When only one player remains, they have won
			return self._active_player_wins()

	def __getstate__(self):
		state = {
			"round": self.round,
			"num_updates": self.num_updates,
			"last_update": int(self.last_update),
			"players": self.players,
			"scores": self.scores,
		}
		if not self.done:
			state["turn_state"] = self.turn_state.to_dict()
			state["active_player"] = self.active_player
		if self.prev_id:
			state["prev_id"] = self.prev_id
		if self.winner:
			state["winner"] = self.winner
		state["id"] = game_state_id(state)

		return state

	def __setstate__(self, state):
		chksum = game_state_id(state)
		if state["id"] != chksum:
			raise ChecksumMismatchException(f'{state["id"]} != {chksum}')

		# Set defaults for optional variables
		self.winner = None
		self.turn_state = None

		turn_state_dict = state.get("turn_state", None)
		if turn_state_dict:
			state["turn_state"] = TurnState.from_dict(turn_state_dict)

		active_player = state.get("active_player", None)
		if active_player:
			state["active_player_index"] = state["players"].index(active_player)
			del state["active_player"]

		self.__dict__.update(state)

	def __str__(self):
		return str(self.__getstate__())

	def as_json(self):
		return json.dumps(self.__getstate__())

	@classmethod
	def from_json(cls, json_string):
		return cls.from_dict(json.loads(json_string))

	@classmethod
	def from_dict(cls, dict):
		self = cls.__new__(cls)
		self.__setstate__(dict)
		return self
