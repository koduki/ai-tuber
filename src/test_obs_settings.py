import asyncio
from obswebsocket import obsws, requests
def run():
    ws = obsws("obs-studio", 4455, "")
    ws.connect()
    resp = ws.call(requests.GetInputSettings(inputName="voice"))
    print("Voice settings:", resp.datain)
    ws.disconnect()
run()
