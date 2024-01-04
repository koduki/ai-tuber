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

prompt_system = open("prompt_system.txt", "r", encoding='utf-8').read()

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(prompt_system),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])


# チャットチェーンの準備
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

#llm = ChatOpenAI(temperature=0)
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
memory = ConversationBufferMemory(return_messages=True)
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm)

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
        res = conversation.predict(input=c.message)
        print(res)
        reply = json.loads(res)
        
        print(f"{datetime.datetime.now()} [紅月あい]: {reply}")
        data, rate = voicevox_adapter.get_voice(reply["character_reply"])
        play_sound.play_sound(data, rate)


