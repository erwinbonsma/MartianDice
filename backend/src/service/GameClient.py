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

def pick_dice(game_id, turn_state):
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
			"game_id": game_id,
			"pick_die": die.name
		})

def check_exit(game_id):
	while True:
		choice = input("Pass (Y/N)? : ").upper()
		if choice == "Y" or choice == "N":
			return json.dumps({
				"action": "move",
				"game_id": game_id,
				"pass": choice == "Y"
			})

def bot_move(game_id, bot_behaviour):
	return json.dumps({
		"action": "bot-move",
		"game_id": game_id,
		"bot_behaviour": bot_behaviour
	})

async def add_bots(ws, game_id, bots):
	game_config = {
		"bots": { f"Bot-{i+1}": behaviour for i, behaviour in enumerate(bots) }
	}
	await ws.send(json.dumps({
		"action": "update-config",
		"game_id": game_id,
		"game_config": game_config
	}))

async def start_game(ws, game_id, bots):
	await ws.send(json.dumps({
		"action": "start-game",
		"game_id": game_id,
		"game_config": {
			"bots": bots
		}
	}))

async def play_game(url, client_id, game_id = None, num_clients = 1, bot_behaviours = None):
	async with websockets.connect(url) as websocket:
		if game_id is None:
			await websocket.send(json.dumps({ "action": "create-room" }))
			response = json.loads(await websocket.recv())
			game_id = response["room_id"]

		await websocket.send(json.dumps({
			"action": "join-room",
			"room_id": game_id,
			"client_id": client_id
		}))

		if bot_behaviours:
			await add_bots(websocket, game_id, bot_behaviours)
		
		bots = set()
		is_host = False
		while True:
			raw_message = await websocket.recv()
			print(raw_message)
			message = json.loads(raw_message)

			if message["type"] == "clients":
				is_host = message["host"] == client_id

				if len(message["clients"]) == num_clients and (
					num_clients > 1 or not bot_behaviours
				):
					await start_game(websocket, game_id, bots)

			if message["type"] == "game-config":
				bots = message["game_config"]["bots"]
				if num_clients == 1:
					await start_game(websocket, game_id, bots)

			if message["type"] == "game-state":
				for turn_state in message["turn_state_transitions"]:
					print(turn_state)
					await asyncio.sleep(1)
				state = message["state"]
				if "winner" in state:
					print(f"{state[winner]} has won!")
					break
				print(state["turn_state"])
				if state["active_player"] == client_id:
					if state["turn_state"]["phase"] == "PickDice":
						await websocket.send(pick_dice(game_id, state["turn_state"]))
					elif state["turn_state"]["phase"] == "CheckPass":
						await websocket.send(check_exit(game_id))
				if is_host and state["active_player"] in bots:
					bot_behaviour = bots[state["active_player"]]
					await websocket.send(bot_move(game_id, bot_behaviour))

parser = argparse.ArgumentParser(description='Basic Martian Dice client')
parser.add_argument('--num-clients', type=int, help='Number of clients (host only)', default=1)
parser.add_argument('--bots', nargs='*', choices=["smart", "random", "defensive", "aggressive"], help='Adds bot(s) (host only)')
parser.add_argument('--name', help='Player name')
parser.add_argument('--url', help='Game service endpoint', default='ws://127.0.0.1:8765')
parser.add_argument('--join-game', dest="game_id", metavar="Game ID", help="Join existing game")
