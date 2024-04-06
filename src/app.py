from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

import os
import sys

from backend.chatai import ChatAI
from frontend.app import App

secret_path = f"{os.environ['HOMEPATH']}/.secret/"
os.environ["OPENAI_API_KEY"] = open(secret_path + "openai.txt", "r").read()
os.environ["OPENAI_API_KEY"] = open(secret_path + "gemini.txt", "r").read()
os.environ["OBS_WS_PASSWORD"] = open(secret_path + "obs.txt", "r").read()

# AI
llm_model = sys.argv[1] if len(sys.argv) > 1 else 'gemini'
ai = ChatAI(llm_model)

# YouTube & OBS, Voice
print("YouTubeのVIDEO_IDを入れてください.")
# video_id = input() # "YOUR_VIDEO_ID"

app = Flask(__name__)

def scheduled_task():
    print("Hello World")

# APSchedulerの初期化とジョブの追加
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_task, 'interval', seconds=5)
scheduler.start()

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
        scheduler.shutdown()
