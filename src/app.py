import os
import json

from backend.chatai import ChatAI
from frontend.aituber import AITuber
from frontend.obs_adapter import ObsAdapter
from frontend.youtube_live_adapter import YoutubeLiveAdapter

from flask import Flask, render_template, request

secret_path = "/secret/"
os.environ["OPENAI_API_KEY"] = open(secret_path + "openai.txt", "r").read()
os.environ["GOOGLE_API_KEY"] = open(secret_path + "gemini.txt", "r").read()
os.environ["OBS_WS_PASSWORD"] = open(secret_path + "obs.txt", "r").read()

# AI
from backend.chatai import ChatAI
ai = ChatAI("gpt4")
aituber = AITuber(ai)

# Start Web
stream_key = None 
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title = 'flask test')

@app.route("/create_stream", methods=["post"])
def create_stream():
    global stream_key
    
    print("click create_stream")
    
    data = json.loads(request.data)
    ytlive = YoutubeLiveAdapter()
    youtube_client = ytlive.authenticate_youtube()

    title = data["title"]
    description = data["description"]
    start_date = data["date"]
    print(start_date)
    thumbnail_path = '/workspaces/ai-tuber/obs_data/ai_normal.png'
    print(thumbnail_path)
    privacy_status = data["privacy_status"]

    live_response = ytlive.create_live(youtube_client, title, description, start_date, thumbnail_path, privacy_status)
    stream_key = live_response['stream']['cdn']['ingestionInfo']['streamName']

    print(f"Stream Key: {stream_key}")  # デバッグ出力
    print(live_response)
    print("/click create_stream")

    return live_response

@app.route("/stop_stream", methods=["post"])
def stop_stream():
    print("click stop_stream")
    obs = ObsAdapter()
    obs.stop_stream()
    print("/click stop_stream")
    # live_response = ytlive.create_live(youtube_client, title, description, start_date, thumbnail_path, "private")

    return {"Message":"Stop stream."}

@app.route("/start_ai", methods=["post"])
def start_ai():
    print("click start_ai")

    data = json.loads(request.data)
    print(data)
    broadcast_id = data["broadcastId"]
    stream_name = data["streamName"]

    obs = ObsAdapter()
    obs.start_stream(stream_name)

    aituber.set_broadcast_id(broadcast_id)
    aituber.exec()

    print("/click start_ai")
    return {"Message":"Start AI."}


if __name__ == '__main__':
    try:
        print("Admin console is `http://localhost:5000/`")
        app.run(use_reloader=False, debug=True, host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # アプリケーションが終了する際に、スケジューラも適切に停止させる
        print("Shutting down...")
        aituber.close()
