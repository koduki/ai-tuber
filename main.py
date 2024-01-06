import os
import sys

from ai_agent import AIAgent
from frontend import Frontend

os.environ["OPENAI_API_KEY"] = open("C:\\Users\\koduki\\.secret\\openai.txt", "r").read()
os.environ["GOOGLE_API_KEY"] = open("C:\\Users\\koduki\\.secret\\gemini.txt", "r").read()
os.environ["OBS_WS_PASSWORD"] = open("C:\\Users\\koduki\\.secret\\obs.txt", "r").read()

llm_model = sys.argv[1] if len(sys.argv) > 1 else 'gemini'
ai = AIAgent(llm_model)

print("YouTubeのVIDEO_IDを入れてください.")
video_id = input() # "YOUR_VIDEO_ID"
frontend = Frontend(ai)
frontend.exec(video_id)