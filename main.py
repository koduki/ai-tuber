import os
import sys

from backend.ai_agent import AIAgent
from frontend.app import App

def read_secret(file_name):
    home_directory = os.path.expanduser("~")
    file_path = os.path.join(home_directory, ".secret", file_name)
    with open(file_path, "r") as file:
        return file.read().strip()

try:
    os.environ["OPENAI_API_KEY"] = read_secret("openai.txt")
    os.environ["GOOGLE_API_KEY"] = read_secret("gemini.txt")
    os.environ["OBS_WS_PASSWORD"] = read_secret("obs.txt")

    # AI
    llm_model = sys.argv[1] if len(sys.argv) > 1 else 'gemini'
    ai = AIAgent(llm_model)

    # YouTube & OBS, Voice
    print("YouTubeのVIDEO_IDを入れてください.")
    video_id = input() # "YOUR_VIDEO_ID"

    app = App(ai)
    app.exec(video_id)
except Exception as e:
    print(e)
    print(e.__traceback__)