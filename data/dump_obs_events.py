import asyncio
import logging
import json
from obswebsocket import obsws, base_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def on_any_event(message):
    try:
        data = message.datain
        logger.info(f"OBS Event: {message.name} - Data: {json.dumps(data)}")
    except Exception as e:
        logger.error(f"Error handling event: {e}")

async def test():
    ws = obsws("obs-studio", 4455, "")
    ws.connect()
    ws.register(on_any_event)
    logger.info("Listening for ALL OBS events... (waiting 10 seconds)")
    
    # Try doing a media reload action
    from obswebsocket import requests
    try:
        ws.call(requests.TriggerMediaInputAction(
            inputName="voice",
            mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
        ))
    except Exception as e:
        logger.warning(f"Could not trigger: {e}")
        
    await asyncio.sleep(10)
    ws.disconnect()

asyncio.run(test())
