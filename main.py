# Setup
import os
os.environ["OPENAI_API_KEY"] = open("C:\\Users\\koduki\\.secret\\openai.txt", "r").read()

# テンプレートとプロンプトエンジニアリング
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from typing import List

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class Reply(BaseModel):
    current_emotion: str = Field(description="maxe")
    character_reply: str = Field(description="あい's reply to User")

parser = JsonOutputParser(pydantic_object=Reply)


prompt_system = open("prompt_system.txt", "r", encoding='utf-8').read()

# prompt = ChatPromptTemplate.from_messages([
#     SystemMessagePromptTemplate.from_template(prompt_system),
#     MessagesPlaceholder(variable_name="history"),
#     HumanMessagePromptTemplate.from_template("{input}"),
# ])

from langchain.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", prompt_system),
    ("user", "{input}")
])

# チャットチェーンの準備
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

# llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
# memory = ConversationBufferMemory(return_messages=True)
# conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm, partial_variables={"format_instructions": parser.get_format_instructions()})
chain = prompt | llm | parser


import pytchat

# YouTubeのライブ配信またはプレミアム動画のURLまたは動画IDを設定
print("YoutubeのVIDEO_IDを入れてください.")
video_id = input() # "YOUR_VIDEO_ID"

chat = pytchat.create(video_id=video_id)

import json
import datetime
from voicevox_adapter import VoicevoxAdapter
from play_sound import PlaySound

play_sound = PlaySound("スピーカー (Realtek(R) Audio)")
voicevox_adapter = VoicevoxAdapter()

print("Ready. Youtubeにコメントしてね。")
while chat.is_alive():
    for c in chat.get().sync_items():
        print(f"{c.datetime} [{c.author.name}]: {c.message}")
        res = chain.invoke({"input": c.message, "format_instructions": parser.get_format_instructions()})
        print("s00")
        print(res)
        print("s01")
        try:
            # print(parser.parse(res))
            print("s02")
            data = str(res).replace("'", "\"")
            print(data)
            print("s03")
            reply = json.loads(data)
        except Exception as e:
            print(type(e))
            print(e.value)
            print(e.__traceback__)
            print(e)
        print("s04")
        print(f"{datetime.datetime.now()} [紅月あい]: {reply}")
        print("s05")
        data, rate = voicevox_adapter.get_voice(reply["character_reply"])
        play_sound.play_sound(data, rate)


