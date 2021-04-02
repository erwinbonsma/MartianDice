import asyncio
from service.GameClient import play_game, parser

args = parser.parse_args()
asyncio.get_event_loop().run_until_complete(play_game(
	url = args.url,
	client_id = args.name,
	game_id = args.game_id,
	num_clients = args.num_clients,
	bot_behaviours = args.bots
))
