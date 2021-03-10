import json
import os
#import elasticache_auto_discovery
from pymemcache.client.hash import HashClient
from pymemcache.client import base

elasticache_config_endpoint = os.getenv('CACHE_CLUSTER')
# nodes = elasticache_auto_discovery.discover(elasticache_config_endpoint)
# nodes = map(lambda x: (x[1], int(x[2])), nodes)
# cache_client = HashClient(nodes)

cache_client = base.Client('mar-ca-xnvk9ngi0xbk.lq2hi0.0001.euw1.cache.amazonaws.com:11211')

def handler(event, context):
	print(f'cache_cluster: {elasticache_config_endpoint}')

	path = event['path']

	key = f'access_count-{path}'
	access_count = cache_client.incr(key, 1, noreply = False)
	if access_count is None:
		access_count = 1
		cache_client.set(key, 1)

	return {
		'statusCode': 200,
		'headers': {
			'Content-Type': 'text/plain'
		},
		'body': f'Hello, CDK! You have hit {path} {access_count} times'
	}