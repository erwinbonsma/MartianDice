import itertools
from service.BaseHandler import GameHandler, HandlerException, ok_message, error_message
from service.Common import is_bot_name, Config
from service.GameState import GameState
from game.DataTypes import TurnPhase, DieFace, TARGET_SCORE
from game.Game import RandomPlayer, AggressivePlayer, DefensivePlayer
from game.OptimalPlay import OptimalActionSelector

bot_behaviours = {
	"random": RandomPlayer(),
	"aggressive": AggressivePlayer(),
	"defensive": DefensivePlayer(),
	"smart": OptimalActionSelector(consider_win_score = True)
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
		if game_state is None or not game_state.awaits_input:
			raise HandlerException(f"Not awaiting a move")

	def check_my_move(self, game_state):
		self.check_expect_move(game_state)
		if game_state.active_player != self.client_id:
			raise HandlerException(f"{self.client_id} tried to move while it's not their turn")

	def check_bot_move(self, game_state):
		self.check_expect_move(game_state)
		if not is_bot_name(game_state.active_player):
			raise HandlerException("Bot move initiated while it's not a bot's turn")

	def check_can_end_turn(self, game_state):
		if game_state.age_in_seconds < Config.MAX_MOVE_TIME_IN_SECONDS:
			raise HandlerException("You cannot yet forcefully end the current turn")

		if is_bot_name(game_state.active_player):
			raise HandlerException("You can only end the turn of a human player")

	def check_can_remove_player(self, game_state):
		if (
			game_state.active_player != self.client_id and
			game_state.age_in_seconds < Config.MAX_MOVE_TIME_IN_SECONDS
		):
			raise HandlerException("You cannot yet remove the active player")

		if is_bot_name(game_state.active_player):
			raise HandlerException("You can only remove human players")

	async def update_state_until_blocked(self, game_state):
		turn_state_transitions = []
		while not (game_state.done or game_state.awaits_input):
			if not hasattr(game_state.turn_state, "skip_when_animating"):
				turn_state_transitions.append(game_state.turn_state)
			game_state.next()

		if game_state.done:
			self.db.log_game_end(self.room.room_id, game_state)

		await self.broadcast(self.game_state_message(game_state, turn_state_transitions))

	async def handle_move(self, game_state, input_value):
		game_state.next(input_value)

		await self.update_state_until_blocked(game_state)

	async def player_move(self, game_state, cmd_message):
		self.check_my_move(game_state)

		if "pick_die" in cmd_message:
			picked = cmd_message["pick_die"].lower()
			if not picked in str2die:
				raise HandlerException(f"Unknown die: {picked}")

			die = str2die[picked]
			if not game_state.turn_state.can_select(die):
				raise HandlerException(f"Cannot select: {picked}")

			player_move = die
		elif "pass" in cmd_message:
			player_move = cmd_message["pass"]
		else:
			raise HandlerException("Unknown move")

		await self.handle_move(game_state, player_move)

	async def bot_move(self, game_state, bot_behaviour):
		self.check_is_host("initiate bot move")
		self.check_bot_move(game_state)

		action_selector = bot_behaviours[bot_behaviour]

		turn_state = game_state.turn_state
		win_score = TARGET_SCORE - game_state.scores[game_state.active_player]

		if turn_state.phase == TurnPhase.PickDice:
			bot_move = action_selector.select_die(turn_state, win_score)
		else:
			bot_move = action_selector.should_stop(turn_state, win_score)

		await self.handle_move(game_state, bot_move)

	async def end_turn(self, game_state):
		self.check_can_end_turn(game_state)

		await self.handle_move(game_state, "end-turn")

	async def remove_player(self, game_state):
		self.check_can_remove_player(game_state)

		game_state.remove_player()
		await self.handle_move(game_state, "end-turn")

	async def start_game(self, game_config):
		self.check_can_configure_game("start game")

		self.logger.info("Starting game")
		bots = game_config["bots"]
		game_state = GameState( itertools.chain(self.clients.values(), bots.keys()) )

		self.room.inc_game_count()
		self.db.log_game_start(self.room.room_id, game_state)

		await self.update_state_until_blocked(game_state)

	async def _handle_game_command(self, cmd_message):
		cmd = cmd_message["action"]

		if cmd == "start-game":
			return await self.start_game(cmd_message["game_config"])

		game_state = GameState.from_dict(cmd_message["game_state"])
		if cmd == "move":
			return await self.player_move(game_state, cmd_message)

		if cmd == "bot-move":
			return await self.bot_move(game_state, cmd_message["bot_behaviour"])

		if cmd == "end-turn":
			return await self.end_turn(game_state)

		if cmd == "remove-player":
			return await self.remove_player(game_state)

		self.logger.warn("Unrecognized command %s", cmd)
