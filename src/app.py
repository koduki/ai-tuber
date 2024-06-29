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
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title = 'flask test')

@app.route("/start_stream", methods=["post"])
def start_stream():
    import sys
    sys.stdout.flush()
    print("click start_stream")

    data = json.loads(request.data)
    ytlive = YoutubeLiveAdapter()
    youtube_client = ytlive.authenticate_youtube()

    title = data["title"]
    description = """AITuber「紅月恋（れん）」の配信テストです。良ければコメントで話しかけてみてください。

    # クレジット＆テクノロジー
    キャラ絵はStable Diffusionで生成しました。
    LLMはChatGPTまたはGemini Proを利用しています。
    BGMはSuno.aiで作成しました。
    音声は「VOICEVOX:猫使ビィ」を利用させていただいています。
    - https://voicevox.hiroshiba.jp/
    - https://nekotukarb.wixsite.com/nekonohako/%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84
    """
    start_date = '2024-06-30T00:00:00.000Z'
    thumbnail_path = '/workspaces/ai-tuber/obs_data/ai_normal.png'

    live_response = ytlive.create_live(youtube_client, title, description, start_date, thumbnail_path, "unlisted")
    stream_key = live_response['stream']['cdn']['ingestionInfo']['streamName']

    obs = ObsAdapter()
    obs.start_stream(stream_key)

    aituber.set_broadcast_id(live_response["broadcast"]["id"])

    print(live_response)
    print("/click start_stream")
    return {"Message":"Start stream."}

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
    aituber.exec()
    print("/click start_ai")
    return {"Message":"Start AI."}


if __name__ == '__main__':
    try:
        print("Admin console is `http://localhost:5000/`")
        app.run(use_reloader=False, debug=False, host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # アプリケーションが終了する際に、スケジューラも適切に停止させる
        print("Shutting down...")
        aituber.close()
