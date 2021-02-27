import asyncio
from service.GameClient import play_game, parser

args = parser.parse_args()
asyncio.get_event_loop().run_until_complete(play_game(args))
