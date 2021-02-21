import itertools
import jsonpickle
import random

TARGET_SCORE = 25

class GameState:

	def __init__(self, player_ids):
		self.players = player_ids[:]
		random.shuffle(self.players)

		self.score = dict((id, 0) for id in player_ids)
		self.round = 0
		self.active_player = self.players[0]
		self.done = False

	def end_round(self, score):
		self.score[self.active_player] += score

	def next_round(self):
		if self.score[self.active_player] >= TARGET_SCORE:
			self.done = True
			self.active_player = None
			return False

		self.round += 1
		self.active_player = self.players[self.round % len(self.players)]
		return True

	def __getstate__(self):
		return dict(itertools.chain(self.__dict__.items(), [("type", "game-state")]))

	def as_json(self):
		return jsonpickle.encode(self, unpicklable = False)
