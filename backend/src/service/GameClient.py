import argparse
import asyncio
import json
import websockets
from game.DataTypes import DieFace
from game.GameIO import HumanPlayer

human_io = HumanPlayer

key2die = {
	"R": DieFace.Ray,
	"C": DieFace.Chicken,
	"H": DieFace.Human,
	"M": DieFace.Cow
}

def pick_dice(turn_state):
	while True:
		key = input("Your choice : ").upper()
		if not key in key2die:
			print("Unrecognized key")
			continue
		die = key2die[key]
		if not die.name in turn_state["throw"]:
			print("Die not in throw")
			continue
		if die != DieFace.Ray and die.name in turn_state["side_dice"]:
			print("Die already selected")
			continue
		return json.dumps({
			"action": "move",
			"pick-die": die.name
		})

def check_exit():
	while True:
		choice = input("Continue (Y/N)? : ").upper()
		if choice == "Y" or choice == "N":
			return json.dumps({
				"action": "move",
				"throw-again": choice == "Y"
			})

async def add_bots(ws, bots):
	for bot in bots:
		await ws.send(json.dumps({
			"action": "add-bot",
			"bot_behaviour": bot
		}))

async def play_game(args):
	uri = "ws://localhost:8765"
	async with websockets.connect(uri) as websocket:
		await websocket.send(args.name)

		await add_bots(websocket, args.bots)

		while True:
			raw_message = await websocket.recv()
			print(raw_message)
			message = json.loads(raw_message)
			if message["type"] == "clients":
				if len(message["clients"]) == args.num_clients:
					await websocket.send(json.dumps({ "action": "start-game"}))

			if message["type"] == "game-state":
				if message["done"]:
					break
				if message["active_player"] != args.name:
					continue
				if message["turn_state"]["phase"] == "PickDice":
					await websocket.send(pick_dice(message["turn_state"]))
				elif message["turn_state"]["phase"] == "CheckExit":
					await websocket.send(check_exit())

parser = argparse.ArgumentParser(description='Basic Martian Dice client')
parser.add_argument('--num-clients', type=int, help='Number of clients (host only)', default=1)
parser.add_argument('--bots', nargs='*', choices=["smart", "random", "defensive"], help='Adds bot(s) (host only)')
parser.add_argument('--name', help='Player name')
args = parser.parse_args()

asyncio.get_event_loop().run_until_complete(play_game(args))
