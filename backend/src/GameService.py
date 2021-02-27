import asyncio
import websockets
from service.GameServer import GameServer

game_server = GameServer()
start_server = websockets.serve(game_server.main, "", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
