const configSettings = {
	//SERVICE_ENDPOINT: 'wss://gv9b6yzx3j.execute-api.eu-west-1.amazonaws.com/dev',
	SERVICE_ENDPOINT: 'ws://127.0.0.1:8765',

	// Timing of turn-phase transition animations (in ms)
	FAST_TRANSITION_DELAY: 100,
	SLOW_TRANSITION_DELAY: 2500,
	TRANSITION_DELAY: 1000,

	// Animation delays for dice throws (in ms)
	THROW_DELAY: 400,
	FIRST_MOVE_DELAY: 100,
	MOVE_DELAY: 750,

	// Period of inactivity after which a turn-end can be forced (in s)
	MAX_MOVE_TIME_IN_SECONDS: 10,
}

export default configSettings;