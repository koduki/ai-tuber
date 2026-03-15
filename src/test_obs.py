import asyncio
import logging
from obswebsocket import obsws, requests, events

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def test():
    loop = asyncio.get_running_loop()
    ws = obsws("obs-studio", 4455, "")
    ws.connect()
    
    def on_started(message):
        print(f"Started: {message.datain}")
        print(f"inputName: {message.getInputName()}")
        
    def on_ended(message):
        print(f"Ended: {message.datain}")
        print(f"inputName: {message.getInputName()}")
        
    ws.register(on_started, events.MediaInputPlaybackStarted)
    ws.register(on_ended, events.MediaInputPlaybackEnded)
    
    print("Triggering media restart...")
    
    # Trigger it
    ws.call(requests.TriggerMediaInputAction(
        inputName="voice",
        mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    ))
    
    await asyncio.sleep(2)
    ws.disconnect()

asyncio.run(test())
