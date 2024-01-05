# Setup
import os
import sys

os.environ["OPENAI_API_KEY"] = open("C:\\Users\\koduki\\.secret\\openai.txt", "r").read()
os.environ["GOOGLE_API_KEY"] = open("C:\\Users\\koduki\\.secret\\gemini.txt", "r").read()
os.environ["OBS_WS_PASSWORD"] = open("C:\\Users\\koduki\\.secret\\obs.txt", "r").read()

# テンプレートとプロンプトエンジニアリング
from langchain.prompts import (
    ChatPromptTemplate,
)

prompt_system = open("prompt_system.txt", "r", encoding='utf-8').read()
prompt = ChatPromptTemplate.from_messages([
    ("system", prompt_system),
    ("user", "{input}")
])

# モデルの準備
from langchain.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

llm_model = sys.argv[1] if len(sys.argv) > 1 else 'gemini'
if llm_model == 'gpt4':
    llm = ChatOpenAI(model_name="gpt-4", temperature=0)
elif llm_model == 'gpt3':
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)
elif llm_model == 'gemini':
    llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
else:
    llm = None


# 出力フォーマットを定義
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class Reply(BaseModel):
    current_emotion: str = Field(description="maxe")
    character_reply: str = Field(description="あい's reply to User")

parser = JsonOutputParser(pydantic_object=Reply)

# チェインを作成
chain = prompt | llm | parser




#
# Frontend
#
import pytchat

# YouTubeのライブ配信またはプレミアム動画のURLまたは動画IDを設定
print("YouTubeのVIDEO_IDを入れてください.")
video_id = input() # "YOUR_VIDEO_ID"

chat = pytchat.create(video_id=video_id)

import time
import json
import datetime
from voicevox_adapter import VoicevoxAdapter
from play_sound import PlaySound
from obs_adapter import ObsAdapter

play_sound = PlaySound("CABLE Input")
voicevox_adapter = VoicevoxAdapter()

obs = ObsAdapter()
obs.visible_avater("normal")
obs.visible_llm(llm_model)

print("Ready. YouTubeにコメントしてね。")

msg = "良く来たの。今日は何をするのじゃ？"
print(f"{datetime.datetime.now()} [紅月あい]: {msg}")
ss = time.perf_counter()
data, rate = voicevox_adapter.get_voice(msg)
se = time.perf_counter()
print((se - ss))
play_sound.play_sound(data, rate)

while chat.is_alive():
    for c in chat.get().sync_items():
        print(f"{c.datetime} [{c.author.name}]: {c.message}")
        
        try:
            ls = time.perf_counter()
            res = chain.invoke({"input": c.message, "format_instructions": parser.get_format_instructions()})
            le = time.perf_counter()
            print((le - ls))

            print("res: " + str(res))

            data = str(res).replace("'", "\"")
            print("transformed: " + data)
            reply = json.loads(data)
            print("parsed: " + str(reply))
            
            print(f"{datetime.datetime.now()} [紅月あい]: {reply}")
            ss = time.perf_counter()
            data, rate = voicevox_adapter.get_voice(reply["character_reply"])
            se = time.perf_counter()
            print((se - ss))

            obs.visible_avater(reply["current_emotion"])
            play_sound.play_sound(data, rate)
            obs.visible_avater("normal")

        except Exception as e:
            print(e)
            print(e.__traceback__)

