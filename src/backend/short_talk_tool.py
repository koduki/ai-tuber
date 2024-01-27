from langchain.agents import tool

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain

@tool
def talk() -> str:
    """
    This tool reply about short-talk(雑談 or 小話). 
    """
    
    return f"talk_contents:'{_talk()}'"

def _talk():
    import random
    
    talks = _update_news()
    index = random.randrange(len(talks))
    url = talks[index]["url"]
    body = _get(url)

    llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
    prompt = ChatPromptTemplate.from_messages([
        ("human", "Please summarize this HTML by 50 words as text. ::: {html}"),
    ])
    chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    r = chain.invoke({"html": str(body)})
    text = r['text'].replace('\n', '')

    return text

def _update_news():
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

    root = _parse_rss("https://www.theguardian.com/world/extreme-weather/rss")
    xs = list(map(lambda item: item.find("link").text, root.findall("channel/item")))
    urls.extend(xs)
    
    root = _parse_rss("https://www.jstage.jst.go.jp/AF05S010NewRssDld?btnaction=JT0041&sryCd=jmsj&rssLang=en")
    xs = list(map(lambda item: item.find('{http://www.w3.org/2005/Atom}link').attrib['href'], root.findall('./{http://www.w3.org/2005/Atom}entry')))
    urls.extend(xs)
    
    
    
    # root = self._parse_rss("https://gigazine.net/news/rss_2.0/")
    # software_items = [item for item in root.findall("channel/item") if "ソフトウェア" in item.find("{http://purl.org/dc/elements/1.1/}subject").text]
    # xs = list(map(lambda item: item.find("link").text, software_items))
    # urls.extend(xs)

    print("finish:update the latest news.")

    return list(map(lambda url: {"url": url, "data": ""}, urls))


def _parse_rss(url):
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
    
def _get(url):
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')    

    # scriptタグとstyleタグをすべて削除
    for script_or_style in soup(["script", "style", "iframe", "svg", "img", "video"]):
        script_or_style.extract()
    
    body_content = soup.body
    if body_content:
        return body_content
    else:
        return 'Body tag not found'