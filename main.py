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

def _say(text):
    import json

    ls = time.perf_counter()
    res = chain.invoke({"input": text, "format_instructions": parser.get_format_instructions()})
    le = time.perf_counter()
    print("llm response(sec): " + str(le - ls))
    print("res: " + str(res))

    text = str(res).replace("'", "\"")
    data = json.loads(text)
    data["current_emotion"] = data["current_emotion"].split(":")[0]
    print("parsed: " + str(data))

    return data

talks = [
    {"url":"https://gigazine.net/news/20240105-niklaus-wirth-passed-away/?s=09","data":""},
    {"url":"https://ja.wikipedia.org/wiki/Stable_Diffusion","data":""},
    {"url":"https://ja.wikipedia.org/wiki/ChatGPT","data":""},
    {"url":"https://www.4gamer.net/games/338/G033856/20231220044/","data":""},
    {"url":"https://www.moguravr.com/snapdragon-xr2-plus-gen-2-revealed/","data":""},
    {"url":"https://www.moguravr.com/vtuber-contents-2023/","data":""},
    {"url":"https://note.com/shi3zblog/n/nf657d6105bd9","data":""},
    {"url":"https://ymmt.hatenablog.com/entry/2024/01/05/165100","data":""},
    {"url":"https://collabo-cafe.com/events/collabo/frieren-anime2023-add-info-2nd-cours/","data":""},
    {"url":"https://gamewith.jp/fgo/article/show/432003","data":""},

    
]

def say_short_talk():
    import random

    index = random.randrange(len(talks))
    if talks[index]["data"] == "":
        url = talks[index]["url"]
        msg = f"""以下のページを参考にリスナーに「ちょっと小話でもしようかの」と言って、600文字程度の雑談をしてください。その際にキャラクターらしさを含めた内容になるようにしてください。
        {url}
        """
        
        talks[index]["data"] = _say(msg)

    return talks[index]["data"]

def say_chat(comment):
    return _say(comment)

#
# Frontend
#

import time
import datetime
from voicevox_adapter import VoicevoxAdapter
from play_sound import PlaySound
from obs_adapter import ObsAdapter

# play_sound = PlaySound("スピーカー (Realtek(R) Audio)")
play_sound = PlaySound("CABLE Input")
voicevox_adapter = VoicevoxAdapter()

obs = ObsAdapter()
obs.visible_avater("normal")
obs.visible_llm(llm_model)

def voice(msg):
    text = msg["character_reply"]
    emotion = msg["current_emotion"]

    print(f"{datetime.datetime.now()} [紅月れん]: {text}")
    ss = time.perf_counter()
    data, rate = voicevox_adapter.get_voice(text)
    se = time.perf_counter()
    print("voice response(sec): " + str(se - ss))

    obs.visible_avater(emotion)
    play_sound.play_sound(data, rate)
    obs.visible_avater("normal")


import pytchat
print("YouTubeのVIDEO_IDを入れてください.")
video_id = input() # "YOUR_VIDEO_ID"
chat = pytchat.create(video_id=video_id)
print("Ready. YouTubeにコメントしてね。")

voice({"character_reply":"良く来たの。今日は何をするのじゃ？", "current_emotion":"joyful"})

import asyncio

def show_error(e):
    print(e)
    print(e.__traceback__)

async def task_chat(q):
    while True:
        await asyncio.sleep(1)
        if chat.is_alive():
            for c in chat.get().sync_items():
                print(f"{c.datetime} [{c.author.name}]: {c.message}")
                try:
                    reply = say_chat(c.message)
                    print("step1")
                    await q.put(reply)
                    print("step1-1")
                except Exception as e:
                    show_error(e)

async def task_short_talk(q):
    while True:
        await asyncio.sleep(60 * 3)
        try:
            reply = say_short_talk()
            print("step2")
            await q.put(reply)
            print("step2-2")
        except Exception as e:
            show_error(e)  

async def task_voice(q):
    while True:
        try:
            print("step3")
            reply = await q.get()
            print("step4")
            voice(reply)
            print("step4-2")
            q.task_done()
        except Exception as e:
            show_error(e)

async def task_system():
    from aioconsole import ainput
    
    while True:
        print("step5")
        syscmd = await ainput()
        print("step5-2")
        if syscmd == "quit" or syscmd == "q":
            print(syscmd)
            exit(0)


async def main():
    q = asyncio.Queue()
    t1 = asyncio.create_task(task_chat(q))
    t2 = asyncio.create_task(task_short_talk(q))
    t3 = asyncio.create_task(task_voice(q))
    t4 = asyncio.create_task(task_system())
    await t1
    await t2
    await t3
    await t4

asyncio.run(main())



