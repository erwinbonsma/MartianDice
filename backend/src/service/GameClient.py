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

def bot_move():
	return json.dumps({
		"action": "bot-move"
	})

async def add_bots(ws, bots):
	for bot in bots:
		await ws.send(json.dumps({
			"action": "add-bot",
			"bot_behaviour": bot
		}))

async def play_game(args):
	async with websockets.connect(args.url) as websocket:
		await websocket.send(args.name)

		bots = set()
		is_host = False

		if args.bots is not None:
			await add_bots(websocket, args.bots)

		while True:
			raw_message = await websocket.recv()
			print(raw_message)
			message = json.loads(raw_message)

			if message["type"] == "clients":
				is_host = message["host"] == args.name

				if len(message["clients"]) == args.num_clients:
					await websocket.send(json.dumps({ "action": "start-game"}))

			if message["type"] == "bots":
				bots = set(message["bots"])

			if message["type"] == "game-state":
				for turn_state in message["turn_state_transitions"]:
					print(turn_state)
					await asyncio.sleep(1)
				state = message["state"]
				if state["done"]:
					break
				if state["active_player"] == args.name:
					if state["turn_state"]["phase"] == "PickDice":
						await websocket.send(pick_dice(state["turn_state"]))
					elif state["turn_state"]["phase"] == "ThrowAgain":
						await websocket.send(check_exit())
				if is_host and state["active_player"] in bots:
					await websocket.send(bot_move())

parser = argparse.ArgumentParser(description='Basic Martian Dice client')
parser.add_argument('--num-clients', type=int, help='Number of clients (host only)', default=1)
parser.add_argument('--bots', nargs='*', choices=["smart", "random", "defensive"], help='Adds bot(s) (host only)')
parser.add_argument('--name', help='Player name')
parser.add_argument('--url', help='Game service endpoint', default='ws://127.0.0.1:8765')
