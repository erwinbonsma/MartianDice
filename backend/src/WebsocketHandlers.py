import asyncio
import boto3
import json
import os
from pymemcache.client import base
from service.BaseHandler import ok_message
from service.DisconnectionHandler import DisconnectionHandler
from service.GamePlayHandler import GamePlayHandler
from service.MetaGameHandler import MetaGameHandler
from service.RegistrationHandler import RegistrationHandler
from service.MemcachedStorage import MemcachedStorage

cache_client = base.Client(os.getenv('CACHE_CLUSTER'))
db = MemcachedStorage(cache_client = cache_client)

REQUEST_HANDLED = { "statusCode": 200 }

class AwsWebsocketComms:
	
	def __init__(self, request_context):
		domain_name = request_context['domainName']
		stage = request_context['stage']
		url = f'https://{domain_name}/{stage}'
		print("url =", url)
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

	print('handle_registration')
	print('connection_id =', connection_id)
	print('event =', json.dumps(event))
	print('message =', message)

	domain_name = request_context['domainName']
	stage = request_context['stage']
	url = f'https://{domain_name}/{stage}'
	print("url =", url)
	gateway_client = boto3.client(
		'apigatewaymanagementapi',
		endpoint_url = url
	)
	gateway_client.post_to_connection(
		ConnectionId = connection_id,
		Data = json.dumps(ok_message({ "room_id": "ABCD" }))
	)

	#handler = RegistrationHandler(db, AwsWebsocketComms(request_context), connection_id)
	#asyncio.get_event_loop().run_until_complete(handler.handle_command(message))

	return REQUEST_HANDLED

def handle_disconnect(event, context):
	request_context = event['requestContext']
	connection_id = request_context['connectionId']

	print('handle_disconnect')
	print('connection_id =', connection_id)
	print('event =', json.dumps(event))

	handler = DisconnectionHandler(db, AwsWebsocketComms(request_context), connection_id)
	asyncio.get_event_loop().run_until_complete(handler.handle_disconnect())
