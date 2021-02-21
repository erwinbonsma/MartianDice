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

def pick_dice(round_state):
	while True:
		key = input("Your choice : ").upper()
		if not key in key2die:
			print("Unrecognized key")
			continue
		die = key2die[key]
		if not die.name in round_state["throw"]:
			print("Die not in throw")
			continue
		if die != DieFace.Ray and die.name in round_state["side_dice"]:
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

async def play_game(player_id):
	uri = "ws://localhost:8765"
	async with websockets.connect(uri) as websocket:
		await websocket.send(str(player_id))

		while True:
			raw_message = await websocket.recv()
			print(raw_message)
			message = json.loads(raw_message)
			if message["type"] == "game-state":
				if message["done"]:
					break
				if message["active_player"] != player_id:
					continue
				if message["round_state"]["phase"] == "PickDice":
					await websocket.send(pick_dice(message["round_state"]))
				elif message["round_state"]["phase"] == "CheckExit":
					await websocket.send(check_exit())

parser = argparse.ArgumentParser(description='Basic Martian Dice client')
parser.add_argument('--game-id', help='Game ID')
parser.add_argument('--player-id', help='Player ID')
args = parser.parse_args()

asyncio.get_event_loop().run_until_complete(play_game(int(args.player_id)))