from datetime import timedelta

class Config:
	MAX_MOVE_TIME_IN_SECONDS = 30
	MAX_NAME_LENGTH = 12
	MAX_CLIENTS_PER_ROOM = 6
	MAX_BOTS_PER_ROOM = 6

	ROOMS_TABLE = "MartianDice-Rooms-dev"
	GAMES_TABLE = "MartianDice-Games-dev"
	ROOM_EXPIRATION = timedelta(days = 1)
