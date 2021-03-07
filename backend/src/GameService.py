import asyncio
import logging
import websockets
from service.LocalGateway import LocalGateway

logging.setLogRecordFactory(logging.LogRecord)

gateway = LocalGateway()
start_server = websockets.serve(gateway.main, "", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
