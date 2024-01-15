import time
import os
from .parse_chain import ParseChain

class ChatAI:
    talks = [
        {"url":"https://gigazine.net/news/20240105-niklaus-wirth-passed-away/?s=09","data":""},
        {"url":"https://ja.wikipedia.org/wiki/Stable_Diffusion","data":""}, 
    ]

    def __init__(self, llm_model) -> None:
        self.use_llm(llm_model)
        self._update_news()

    def _update_news(self):

        urls=[]
        print("start:update the latest news.")

        root = self._parse_rss("https://www.moguravr.com/feed/")
        xs = list(map(lambda item: item.find("link").text, root.findall("channel/item")))
        urls.extend(xs)

        root = self._parse_rss("https://animeanime.jp/rss20/index.rdf")
        xs = list(map(lambda item: item.find("link").text, root.findall("channel/item")))
        urls.extend(xs)

        root = self._parse_rss("https://b.hatena.ne.jp/entrylist/it.rss")
        xs = list(map(lambda item: item.find('{http://purl.org/rss/1.0/}link').text, root.findall('./{http://purl.org/rss/1.0/}item')))
        urls.extend(xs)

        # root = self._parse_rss("https://gigazine.net/news/rss_2.0/")
        # software_items = [item for item in root.findall("channel/item") if "ソフトウェア" in item.find("{http://purl.org/dc/elements/1.1/}subject").text]
        # xs = list(map(lambda item: item.find("link").text, software_items))
        # urls.extend(xs)

        self.talks = list(map(lambda url: {"url": url, "data": ""}, urls))

        print("finish:update the latest news.")


    def _parse_rss(self, url):
        import requests
        import xml.etree.ElementTree as ET

        """指定されたURLからRSSフィードを取得して解析します。"""
        response = requests.get(url)
        if response.status_code == 200:
            rss_xml = response.content
            root = ET.fromstring(rss_xml)
            return root
        else:
            raise Exception("RSSフィードの取得に失敗しました")
    
    def use_llm(self, llm_model):
        self.llm_model = llm_model
        print("use model: " + llm_model)

        # 出力フォーマットを定義
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.pydantic_v1 import BaseModel, Field

        class Reply(BaseModel):
            current_emotion: str = Field(description="maxe")
            character_reply: str = Field(description="れん's reply to User")

        parser = JsonOutputParser(pydantic_object=Reply)

        # テンプレートとプロンプトエンジニアリング
        from langchain.prompts import (
            ChatPromptTemplate,
            HumanMessagePromptTemplate,
            SystemMessagePromptTemplate,
            MessagesPlaceholder,
        )

        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'prompt_system.txt')
        prompt_system = open(file_path, "r", encoding='utf-8').read()

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(prompt_system),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"), 
        ]).partial(format_instructions=parser.get_format_instructions())

        # モデルの準備
        from langchain_community.chat_models import ChatOpenAI
        from langchain_google_genai import ChatGoogleGenerativeAI

        if llm_model == 'gpt4':
            llm = ChatOpenAI(model_name="gpt-4", temperature=0)
        elif llm_model == 'gpt3':
            llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)
        elif llm_model == 'gemini':
            llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
        else:
            llm = None

        # チェインを作成
        from langchain.chains import LLMChain
        from langchain.memory import ConversationBufferWindowMemory
        memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=20)
        chain = LLMChain(llm=llm, prompt=prompt, verbose=False, memory=memory)
        self.chat_chain = ParseChain(chain=chain, verbose=False)

    #
    # methods
    #
    def _say(self, text):
        print("start:llm")
        ls = time.perf_counter()
        res = self.chat_chain.invoke({"input": text})
        le = time.perf_counter()
        print("finish:llm response(sec): " + str(le - ls))
        print("res: " + str(res))

        return res

    def say_short_talk(self):
        import random

        index = random.randrange(len(self.talks))
        if self.talks[index]["data"] == "":
            url = self.talks[index]["url"]
            msg = f"""以下のページを参考にリスナーに「ちょっと小話でもしようかの」と言って、600文字程度の雑談をしてください。その際にキャラクターらしさを含めた内容になるようにしてください。
            {url}
            """
            
            self.talks[index]["data"] = self._say(msg)

        return self.talks[index]["data"]

    def say_chat(self, comment):
        return self._say(comment)

