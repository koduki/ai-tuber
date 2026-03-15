import asyncio
from obswebsocket import obsws, requests

async def test():
    ws = obsws("obs-studio", 4455, "")
    ws.connect()
    
    scene = ws.call(requests.GetCurrentProgramScene()).getSceneName()
    
    def on_event(message):
        print(f"EVENT: {type(message).__name__}")
        
    ws.register(on_event)
    
    print("Restarting media...")
    ws.call(requests.TriggerMediaInputAction(
        inputName="voice",
        mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    ))
    
    await asyncio.sleep(5)
    ws.disconnect()

asyncio.run(test())
