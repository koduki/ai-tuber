import os
import json

from backend.chatai import ChatAI
from frontend.aituber import AITuber

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
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title = 'flask test')

@app.route("/start", methods=["post"])
def start():
    data = json.loads(request.data)
    video_id = data.get("video_id")

    # YouTube & OBS, Voice
    aituber.exec(video_id)

    return {"message":"Success: " + video_id}

if __name__ == '__main__':
    try:
        print("Admin console is `http://localhost:5000/`")
        app.run(use_reloader=False, debug=True, port=5000)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # アプリケーションが終了する際に、スケジューラも適切に停止させる
        print("Shutting down...")
        aituber.close()
