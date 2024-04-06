import os
import sys

from backend.chatai import ChatAI
from frontend.app import App

def read_secret(file_name):
    home_directory = os.path.expanduser("~")
    file_path = os.path.join(home_directory, ".secret", file_name)
    with open(file_path, "r") as file:
        return file.read().strip()
    
from flask import Flask
console = Flask(__name__)

@console.route('/')
def index():
    return "Flask and APScheduler Example!"


os.environ["OPENAI_API_KEY"] = read_secret("openai.txt")
os.environ["GOOGLE_API_KEY"] = read_secret("gemini.txt")
os.environ["OBS_WS_PASSWORD"] = read_secret("obs.txt")

# # AI
llm_model = sys.argv[1] if len(sys.argv) > 1 else 'gemini'
ai = ChatAI(llm_model)

# # YouTube & OBS, Voice
print("YouTubeのVIDEO_IDを入れてください.")
video_id = input() # "YOUR_VIDEO_ID"

app = App(ai)
app.exec(video_id)

if __name__ == '__main__':
    try:
        console.run(use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        app.close()