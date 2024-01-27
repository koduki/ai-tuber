from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain

class ShortTalkEngine:
    talks = [
        {"url":"https://gigazine.net/news/20240105-niklaus-wirth-passed-away/?s=09","data":""},
        {"url":"https://ja.wikipedia.org/wiki/Stable_Diffusion","data":""}, 
    ]

    def __init__(self):
        self.talks = []

    @staticmethod
    def _get(url):
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')    

        # scriptタグとstyleタグをすべて削除
        for script_or_style in soup(["script", "style", "iframe", "svg", "img", "video"]):
            script_or_style.extract()  # タグを取り除く
        
        body_content = soup.body
        if body_content:
            return body_content # bodyタグのテキスト内容のみを返す
        else:
            return 'Body tag not found'
    

    def neta(self):
        import random

        index = random.randrange(len(self.talks))
        url = self.talks[index]["url"]
        body = ShortTalkEngine._get(url)

        llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
        prompt = ChatPromptTemplate.from_messages([
            ("human", "Please summarize this HTML by 50 words as text. ::: {html}"),
        ])
        chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
        r = chain.invoke({"html": str(body)})
        text = r['text']

        return text
    
    def update_news(self):

        urls=[]
        print("start:update the latest news.")

        urls.extend(['https://ja.wikipedia.org/wiki/%E6%B0%97%E8%B1%A1%E7%B2%BE%E9%9C%8A%E8%A8%98'])
        # root = self._parse_rss("https://www.moguravr.com/feed/")
        # xs = list(map(lambda item: item.find("link").text, root.findall("channel/item")))
        # urls.extend(xs)

        # root = self._parse_rss("https://animeanime.jp/rss20/index.rdf")
        # xs = list(map(lambda item: item.find("link").text, root.findall("channel/item")))
        # urls.extend(xs)

        # root = self._parse_rss("https://b.hatena.ne.jp/entrylist/it.rss")
        # xs = list(map(lambda item: item.find('{http://purl.org/rss/1.0/}link').text, root.findall('./{http://purl.org/rss/1.0/}item')))
        # urls.extend(xs)

        root = self._parse_rss("https://www.theguardian.com/world/extreme-weather/rss")
        xs = list(map(lambda item: item.find("link").text, root.findall("channel/item")))
        urls.extend(xs)
        
        root = self._parse_rss("https://www.jstage.jst.go.jp/AF05S010NewRssDld?btnaction=JT0041&sryCd=jmsj&rssLang=en")
        xs = list(map(lambda item: item.find('{http://www.w3.org/2005/Atom}link').attrib['href'], root.findall('./{http://www.w3.org/2005/Atom}entry')))
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