import itertools
import json
from service.BaseHandler import GameHandler, HandlerException, ok_message, error_message
from service.GameState import GameState
from game.DataTypes import TurnState, TurnPhase, DieFace
from game.Game import RandomPlayer, DefensivePlayer
from game.OptimalPlay import OptimalActionSelector

bot_behaviours = {
	"random": RandomPlayer(),
	"defensive": DefensivePlayer(),
	"smart": OptimalActionSelector()
}

str2die = {
	"ray": DieFace.Ray,
	"chicken": DieFace.Chicken,
	"cow": DieFace.Cow,
	"human": DieFace.Human
}

class GamePlayHandler(GameHandler):
	"""Handles game play."""

	def check_expect_move(self, game_state):
		if game_state is None or not game_state.awaitsInput:
			raise HandlerException(f"Not awaiting a move")

	def check_my_move(self, game_state):
		self.check_expect_move(game_state)
		if game_state.active_player != self.client_id:
			raise HandlerException(f"{self.client_id} tried to move while it's not their turn")

	def check_bot_move(self, game_state, bots):
		self.check_expect_move(game_state)
		if not game_state.active_player in bots:
			raise HandlerException("Bot move initiated while it's not a bot's turn")

	async def update_state_until_blocked(self, game_state):
		turn_state_transitions = []
		while not (game_state.done or game_state.awaitsInput):
			if not hasattr(game_state.turn_state, "skip_when_animating"):
				turn_state_transitions.append(game_state.turn_state)
			game_state.next()

		if self.game.set_state(game_state):
			await self.broadcast(self.game_state_message(game_state, turn_state_transitions))

	async def handle_move(self, game_state, input_value):
		game_state.next(input_value)

		await self.update_state_until_blocked(game_state)

	async def player_move(self, cmd_message):
		game_state = self.game.state()
		self.check_my_move(game_state)

		if "pick_die" in cmd_message:
			picked = cmd_message["pick_die"].lower()
			if not picked in str2die:
				raise HandlerException(f"Unknown die: {picked}")

			die = str2die[picked]
			if not game_state.turn_state.can_select(die):
				raise HandlerException(f"Cannot select: {picked}")

			player_move = die
		elif "throw_again" in cmd_message:
			player_move = not cmd_message["throw_again"]
		else:
			raise HandlerException("Unknown move")

		await self.handle_move(game_state, player_move)

	async def bot_move(self):
		self.check_is_host("initiate bot move")

		game_state = self.game.state()
		bots = self.game.bots()
		self.check_bot_move(game_state, bots)
		
		action_selector = bot_behaviours[bots[game_state.active_player]]

		turn_state = game_state.turn_state
		if turn_state.phase == TurnPhase.PickDice:
			bot_move = action_selector.select_die(turn_state)
		else:
			bot_move = action_selector.should_stop(turn_state)

		await self.handle_move(game_state, bot_move)

	async def start_game(self):
		self.check_can_configure_game("start game")

		self.logger.info("Starting game")
		bots = self.game.bots()
		game_state = GameState( itertools.chain(self.clients.values(), bots.keys()) )

		await self.update_state_until_blocked(game_state)

	async def handle_game_command(self, cmd_message):
		cmd = cmd_message["action"]

		if cmd == "start-game":
			return await self.start_game()

		if cmd == "move":
			return await self.player_move(cmd_message)

		if cmd == "bot-move":
			return await self.bot_move()

		logger.warn(f"Urecognized command {cmd}")
