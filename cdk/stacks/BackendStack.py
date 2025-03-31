from aws_cdk import (
    Aws, Duration, Stack,
    aws_iam as iam,
    aws_apigatewayv2 as apigateway,
    aws_apigatewayv2_integrations as apigateway_integrations,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda
)
from constructs import Construct


class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stage_name = 'dev'

        rooms_table = dynamodb.Table(
            self, "RoomsTable",
            table_name=f"MartianDice-Rooms-{stage_name}",
            partition_key=dynamodb.Attribute(
                name="PKEY",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SKEY",
                type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="TTL",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # As the game is not expected to be popular, set capacities
            # that allow demoing the stack without supporting a large
            # user base.
            max_read_request_units=5,
            max_write_request_units=5,
        )

        games_table = dynamodb.Table(
            self, "GamesTable",
            table_name=f"MartianDice-Games-{stage_name}",
            partition_key=dynamodb.Attribute(
                name="PKEY",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SKEY",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # Capacities can be low here as well, as the implementation is such
            # that database usage is minimized (player turn actions do not
            # trigger database updates)
            max_read_request_units=5,
            max_write_request_units=5,
        )

        main_layer = _lambda.LayerVersion(
            self, 'MainLayer',
            code=_lambda.AssetCode('../backend/layers/main_layer'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11]
        )

        shared_lambda_cfg = {
            "runtime": _lambda.Runtime.PYTHON_3_11,
            "layers": [main_layer],
        }

        registration_handler = _lambda.Function(
            self, 'RegistrationLambda',
            **shared_lambda_cfg,
            code=_lambda.Code.from_asset('../backend/src'),
            handler='WebsocketHandlers.handle_registration',
        )
        rooms_table.grant_read_write_data(registration_handler)

        meta_game_handler = _lambda.Function(
            self, 'MetaGameLambda',
            **shared_lambda_cfg,
            code=_lambda.Code.from_asset('../backend/src'),
            handler='WebsocketHandlers.handle_meta_game',
        )
        rooms_table.grant_read_write_data(meta_game_handler)
        games_table.grant_read_data(meta_game_handler)

        game_play_handler = _lambda.Function(
            self, 'GamePlayLambda',
            **shared_lambda_cfg,
            code=_lambda.Code.from_asset('../backend/src'),
            handler='WebsocketHandlers.handle_game_play',
            timeout=Duration.seconds(10)
        )
        rooms_table.grant_read_write_data(game_play_handler)
        games_table.grant_read_write_data(game_play_handler)

        disconnect_handler = _lambda.Function(
            self, 'DisconnectLambda',
            **shared_lambda_cfg,
            code=_lambda.Code.from_asset('../backend/src'),
            handler='WebsocketHandlers.handle_disconnect',
        )
        rooms_table.grant_read_write_data(disconnect_handler)

        api = apigateway.WebSocketApi(
            self, 'MartianDiceApi',
            default_route_options=apigateway.WebSocketRouteOptions(
                integration=apigateway_integrations.WebSocketLambdaIntegration(
                    'MetaGameHandler',
                    handler=meta_game_handler
                )
            ),
            disconnect_route_options=apigateway.WebSocketRouteOptions(
                integration=apigateway_integrations.WebSocketLambdaIntegration(
                    'DisconnectHandler',
                    handler=disconnect_handler
                )
            ),
            # route_selection_expression = ‘request.body.action’
        )

        registration_integration = apigateway_integrations.WebSocketLambdaIntegration(
            'RegistrationHandler',
            handler=registration_handler
        )
        api.add_route('create-room', integration=registration_integration)

        game_play_integration = apigateway_integrations.WebSocketLambdaIntegration(
            'GamePlayHandler',
            handler=game_play_handler
        )
        for game_cmd in ["start-game", "move", "bot-move", "end-turn", "remove-player"]:
            api.add_route(game_cmd, integration=game_play_integration)

        handlers = [
            registration_handler, meta_game_handler, game_play_handler, disconnect_handler
        ]

        api_gateway_arn = f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{api.api_id}/{stage_name}/*"
        websocket_send_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["execute-api:ManageConnections"],
            resources=[api_gateway_arn],
        )

        for handler in handlers:
            handler.add_to_role_policy(websocket_send_statement)
            handler.add_permission(
                'LambdaInvokePermission',
                principal=iam.ServicePrincipal('apigateway.amazonaws.com'),
                source_arn=api_gateway_arn
            )

        api_stage = apigateway.WebSocketStage(
            self, 'dev-stage',
            web_socket_api=api,
            stage_name=stage_name,
            auto_deploy=True
        )
