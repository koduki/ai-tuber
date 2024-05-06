from flask import Flask

import os

from backend.chatai import ChatAI
from frontend.app import AITuber

secret_path = f"{os.environ['HOMEPATH']}/.secret/"
os.environ["OPENAI_API_KEY"] = open(secret_path + "openai.txt", "r").read()
os.environ["GOOGLE_API_KEY"] = open(secret_path + "gemini.txt", "r").read()
os.environ["OBS_WS_PASSWORD"] = open(secret_path + "obs.txt", "r").read()

# AI
from backend.chatai import ChatAI
ai = ChatAI("gpt4")
aituber = AITuber(ai)

# YouTube & OBS, Voice
print("YouTubeのVIDEO_IDを入れてください.")
video_id = input() # "YOUR_VIDEO_ID"
aituber.exec(video_id)

# Start Web
app = Flask(__name__)
print("Admin console is `http://localhost:5000/`")

@app.route('/')
def index():
    return "Flask and APScheduler Example!"

if __name__ == '__main__':
    try:
        app.run(use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # アプリケーションが終了する際に、スケジューラも適切に停止させる
        print("Shutting down...")
        aituber.close()
