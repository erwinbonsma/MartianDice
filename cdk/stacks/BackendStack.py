from aws_cdk import (
    core,
	aws_iam as iam,
	aws_apigatewayv2 as apigateway,
	aws_apigatewayv2_integrations as apigateway_integrations,
	aws_dynamodb as dynamodb,
	aws_lambda as _lambda
)

class BackendStack(core.Stack):

	def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		stage_name = 'dev'

		rooms_table = dynamodb.Table(
			self, "RoomsTable",
			table_name = f"MartianDice-Rooms-{stage_name}",
			partition_key = dynamodb.Attribute(
				name = "PKEY",
				type = dynamodb.AttributeType.STRING
			),
			sort_key = dynamodb.Attribute(
				name = "SKEY",
				type = dynamodb.AttributeType.STRING
            ),
			time_to_live_attribute = "TTL"
        )

		games_table = dynamodb.Table(
			self, "GamesTable",
			table_name = f"MartianDice-Games-{stage_name}",
			partition_key = dynamodb.Attribute(
				name = "PKEY",
				type = dynamodb.AttributeType.STRING
			),
			sort_key = dynamodb.Attribute(
				name = "SKEY",
				type = dynamodb.AttributeType.STRING
            ),
        )

		main_layer = _lambda.LayerVersion(
			self, 'MainLayer',
			code = _lambda.AssetCode('../backend/layers/main_layer'),
			compatible_runtimes = [_lambda.Runtime.PYTHON_3_9]
		)

		shared_lambda_cfg = {
			"runtime": _lambda.Runtime.PYTHON_3_9,
			"layers": [main_layer],
		}

		registration_handler = _lambda.Function(
			self, 'RegistrationLambda',
			**shared_lambda_cfg,
			code = _lambda.Code.from_asset('../backend/src'),
			handler = 'WebsocketHandlers.handle_registration',
		)
		rooms_table.grant_read_write_data(registration_handler)

		meta_game_handler = _lambda.Function(
			self, 'MetaGameLambda',
			**shared_lambda_cfg,
			code = _lambda.Code.from_asset('../backend/src'),
			handler = 'WebsocketHandlers.handle_meta_game',
		)
		rooms_table.grant_read_write_data(meta_game_handler)
		games_table.grant_read_data(meta_game_handler)

		game_play_handler = _lambda.Function(
			self, 'GamePlayLambda',
			**shared_lambda_cfg,
			code = _lambda.Code.from_asset('../backend/src'),
			handler = 'WebsocketHandlers.handle_game_play',
			timeout = core.Duration.seconds(10)
		)
		rooms_table.grant_read_write_data(game_play_handler)
		games_table.grant_read_write_data(game_play_handler)

		disconnect_handler = _lambda.Function(
			self, 'DisconnectLambda',
			**shared_lambda_cfg,
			code = _lambda.Code.from_asset('../backend/src'),
			handler = 'WebsocketHandlers.handle_disconnect',
		)
		rooms_table.grant_read_write_data(disconnect_handler)

		api = apigateway.WebSocketApi(
			self, 'MartianDiceApi',
			default_route_options = apigateway.WebSocketRouteOptions(
				integration = apigateway_integrations.WebSocketLambdaIntegration(
					'MetaGameHandler',
					handler = meta_game_handler
				)
			),
			disconnect_route_options = apigateway.WebSocketRouteOptions(
				integration = apigateway_integrations.WebSocketLambdaIntegration(
					'DisconnectHandler',
					handler = disconnect_handler
				)
			),
			#route_selection_expression = ‘request.body.action’
		)

		registration_integration = apigateway_integrations.WebSocketLambdaIntegration(
			'RegistrationHandler',
			handler = registration_handler
		)
		api.add_route('create-room', integration = registration_integration)

		game_play_integration = apigateway_integrations.WebSocketLambdaIntegration(
			'GamePlayHandler',
			handler = game_play_handler
		)
		for game_cmd in ["start-game", "move", "bot-move", "end-turn", "remove-player"]:
			api.add_route(game_cmd, integration = game_play_integration)

		websocket_send_statement = iam.PolicyStatement(
			effect = iam.Effect.ALLOW,
			actions = ["execute-api:ManageConnections"],
			resources = [f"arn:aws:execute-api:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:{api.api_id}/{stage_name}/*"],
		)

		registration_handler.add_to_role_policy(websocket_send_statement)
		meta_game_handler.add_to_role_policy(websocket_send_statement)
		game_play_handler.add_to_role_policy(websocket_send_statement)
		disconnect_handler.add_to_role_policy(websocket_send_statement)

		api_stage = apigateway.WebSocketStage(
			self, 'dev-stage',
			web_socket_api = api,
			stage_name = stage_name,
			auto_deploy = True
		)