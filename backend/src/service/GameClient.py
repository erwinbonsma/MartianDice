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

def pick_dice(game_id, game_state):
	turn_state = game_state["turn_state"]
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
			"game_state": game_state,
			"pick_die": die.name
		})

def check_exit(game_id, game_state):
	while True:
		choice = input("Pass (Y/N)? : ").upper()
		if choice == "Y" or choice == "N":
			return json.dumps({
				"action": "move",
				"game_id": game_id,
				"game_state": game_state,
				"pass": choice == "Y"
			})

def bot_move(game_id, game_state, bot_behaviour):
	return json.dumps({
		"action": "bot-move",
		"game_id": game_id,
		"game_state": game_state,
		"bot_behaviour": bot_behaviour
	})

async def add_bots(ws, room_id, bots):
	game_config = {
		"bots": { f"Bot-{i+1}": behaviour for i, behaviour in enumerate(bots) }
	}
	await ws.send(json.dumps({
		"action": "update-config",
		"room_id": room_id,
		"game_config": game_config
	}))

async def start_game(ws, room_id, bots):
	await ws.send(json.dumps({
		"action": "start-game",
		"room_id": room_id,
		"game_config": {
			"bots": bots
		}
	}))

async def welcome_new_clients(ws, room_id, new_clients, bots):
	print("Welcoming", new_clients)
	await ws.send(json.dumps({
		"action": "send-welcome",
		"room_id": room_id,
		"to_clients": new_clients,
		"game_config": {
			"bots": bots
		}
	}))

async def play_game(url, client_id, room_id = None, num_clients = 1, bot_behaviours = None):
	async with websockets.connect(url) as websocket:
		if room_id is None:
			await websocket.send(json.dumps({ "action": "create-room" }))
			response = json.loads(await websocket.recv())
			room_id = response["room_id"]

		await websocket.send(json.dumps({
			"action": "join-room",
			"room_id": room_id,
			"client_id": client_id
		}))

		bots = {}
		clients = set([client_id])
		is_host = False
		game_state = None
		while True:
			raw_message = await websocket.recv()
			print(raw_message)
			message = json.loads(raw_message)

			if message["type"] == "clients":
				is_host = message["host"] == client_id

				clients_prev, clients = clients, set(message["clients"])
				if is_host:
					new_clients = list(clients - clients_prev)
					if new_clients:
						await welcome_new_clients(websocket, room_id, new_clients, bots)

					if bot_behaviours and not bots:
						await add_bots(websocket, room_id, bot_behaviours)		

				if len(message["clients"]) == num_clients and (
					num_clients > 1 or not bot_behaviours
				):
					await start_game(websocket, room_id, bots)

			if message["type"] == "game-config":
				bots = message["game_config"]["bots"]
				if is_host and num_clients == 1:
					print("Starting game")
					await start_game(websocket, room_id, bots)

			if message["type"] == "game-state":
				for turn_state in message["turn_state_transitions"]:
					print(turn_state)
					await asyncio.sleep(1)
				prev_game_state, game_state = game_state, message["state"]
				if prev_game_state:
					assert(prev_game_state["id"] == game_state["prev_id"])
				
				if "winner" in game_state:
					print(f"{game_state[winner]} has won!")
					break

				if game_state["active_player"] == client_id:
					if game_state["turn_state"]["phase"] == "PickDice":
						await websocket.send(pick_dice(room_id, game_state))
					elif game_state["turn_state"]["phase"] == "CheckPass":
						await websocket.send(check_exit(room_id, game_state))
				if is_host and game_state["active_player"] in bots:
					bot_behaviour = bots[game_state["active_player"]]
					await websocket.send(bot_move(room_id, game_state, bot_behaviour))

parser = argparse.ArgumentParser(description='Basic Martian Dice client')
parser.add_argument('--num-clients', type=int, help='Number of clients (host only)', default=1)
parser.add_argument('--bots', nargs='*', choices=["smart", "random", "defensive", "aggressive"], help='Adds bot(s) (host only)')
parser.add_argument('--name', help='Player name')
parser.add_argument('--url', help='Game service endpoint', default='ws://127.0.0.1:8765')
parser.add_argument('--join-room', dest="room_id", metavar="Room ID", help="Join existing room")
