import asyncio
import boto3
import json
import os
from service.BaseHandler import ok_message
from service.DisconnectionHandler import DisconnectionHandler
from service.GamePlayHandler import GamePlayHandler
from service.MetaGameHandler import MetaGameHandler
from service.RegistrationHandler import RegistrationHandler
from service.DynamoDbStorage import DynamoDbStorage

db = DynamoDbStorage()

REQUEST_HANDLED = { "statusCode": 200 }

class AwsWebsocketComms:
	
	def __init__(self, request_context):
		domain_name = request_context['domainName']
		stage = request_context['stage']
		url = f'https://{domain_name}/{stage}'
		self.gateway_client = boto3.client(
			'apigatewaymanagementapi',
			endpoint_url = url
		)

	async def send(self, connection_id, message):
		print(f"sending to {connection_id}")
		self.gateway_client.post_to_connection(
			ConnectionId = connection_id,
			Data = message
		)
		print("message sent")

def handle_registration(event, context):
	request_context = event['requestContext']
	connection_id = request_context['connectionId']
	message = json.loads(event['body'])

	handler = RegistrationHandler(db, AwsWebsocketComms(request_context), connection_id)
	asyncio.get_event_loop().run_until_complete(handler.handle_command(message))

	return REQUEST_HANDLED

def handle_meta_game(event, context):
	request_context = event['requestContext']
	connection_id = request_context['connectionId']
	message = json.loads(event['body'])

	handler = MetaGameHandler(db, AwsWebsocketComms(request_context), connection_id)
	asyncio.get_event_loop().run_until_complete(handler.handle_command(message))

	return REQUEST_HANDLED

def handle_game_play(event, context):
	request_context = event['requestContext']
	connection_id = request_context['connectionId']
	message = json.loads(event['body'])

	handler = GamePlayHandler(db, AwsWebsocketComms(request_context), connection_id)
	asyncio.get_event_loop().run_until_complete(handler.handle_command(message))

	return REQUEST_HANDLED

def handle_disconnect(event, context):
	request_context = event['requestContext']
	connection_id = request_context['connectionId']

	handler = DisconnectionHandler(db, AwsWebsocketComms(request_context), connection_id)
	asyncio.get_event_loop().run_until_complete(handler.handle_disconnect())

	return REQUEST_HANDLED
