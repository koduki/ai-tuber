from langchain.agents import tool
from langchain.prompts import ChatPromptTemplate


# tool デコレーターを使ってツールを定義
@tool
def weather_api(when:str, location: str) -> str:
    """
    This tool answer about weather. 
    argument is [location] and [when]. 
    Default [when] is today
    """
    
    return _weather_api(when, location)

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

def _weather_api(when, location):
    from datetime import date
    today = date.today()
    
    # llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)
    # llm = ChatOpenAI(model="gpt-4", temperature=0)
    llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
    
    from langchain.chains import LLMChain
    prompt = ChatPromptTemplate.from_messages([
        ("system", "今日は{today}です。以下の問に答えなさい。返答のフォーマットは'YYYY-MM-DD'です。返答は'YYYY-MM-DD'のみを返してください。それ以外の値を返すと罰せられます。"),
        ("human", "「{date}」は何日ですか？"),
    ])
    chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    r = chain.invoke({"today": today.strftime('%Y-%m-%d'), "date": when})
    target_date  = r['text']
    
    
    from langchain.chains import LLMChain
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        あなたは地理の専門家です。指定された地域の緯度と経度を
        latitude:xx.xxx, longitude:xxx.xxx
        の形式で回答してください。
        """),
        ("human", "{location}"),
    ])
    chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    r = chain.invoke({"location": location})
    pos = dict((k, v) for k, v in (item.split(':') for item in r['text'].split(', ')))
    
    
    import requests
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={pos['latitude']}&longitude={pos['longitude']}&hourly=temperature_2m,weather_code&timezone=Asia%2FTokyo&start_date={target_date}&end_date={target_date}"
        print("request: " + url)
        response = requests.get(url)
        data = response.json()
        
        import statistics
        temperature = data["hourly"]["temperature_2m"]
        temp_min = min(temperature)
        temp_max = max(temperature)
        temp_avg = statistics.mean(temperature)
        
        wmo_4501_table = {'00': '晴れ', '01': '曇り', '02': '霧', '03': '雨', '04': '雪', '05': '雷雨', '06': '霧雨', '07': '雪雨', '08': '霧', '09': '霧', '10': '霧', '11': '霧', '12': '霧', '13': '霧', '14': '霧', '15': '雨', '16': '雪', '17': '雨', '18': '雪', '19': '雷雨', '20': '晴れ', '21': '曇り', '22': '雨', '23': '雪', '24': '雨', '25': '雪', '26': '雷雨', '27': '霧雨', '28': '雪', '29': '雨', '30': '霧雨', '31': '霧雨', '32': '晴れ', '33': '曇り', '34': '雨', '35': '雪', '36': '雨', '37': '雪', '38': '雷雨', '39': '霧', '40': '雨', '41': '雨', '42': '晴れ', '43': '曇り', '44': '霧雨', '45': '雪', '46': '雨', '47': '雪', '48': '雷雨', '49': '霧', '50': '雪', '51': '雪', '52': '晴れ', '53': '曇り', '54': '霧雨', '55': '雨', '56': '雨', '57': '雪', '58': '雷雨', '59': '霧', '60': '雨', '61': '雨', '62': '晴れ', '63': '曇り', '64': '霧雨', '65': '雨', '66': '雪', '67': '雨', '68': '雷雨', '69': '霧', '70': '雪', '71': '雪', '72': '晴れ', '73': '曇り', '74': '霧雨', '75': '雨', '76': '雪', '77': '雨', '78': '雷雨', '79': '霧', '80': '雨', '81': '雨', '82': '雨', '83': '雨', '84': '雨', '85': '雪', '86': '雪', '87': '雪', '88': '雪', '89': '雷雨', '90': '雷雨', '91': '雷雨', '92': '雷雨', '93': '雷雨', '94': '雷雨', '95': '雷雨', '96': '雷雨', '97': '雷雨', '98': '雷雨', '99': '雷雨'}
        
        from collections import Counter
        
        weather_code = data["hourly"]["weather_code"]
        
        most_common_code = Counter(weather_code).most_common(1)[0][0]
        most_common_code_str = str(most_common_code).zfill(2)
        weather = wmo_4501_table[most_common_code_str]
        
        
        return {'temperature':{'max':temp_max, 'min':temp_min, 'mean':temp_avg}, 'weather':weather, 'date':target_date, 'location':location}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'temperature':{'max':'unknown', 'min':'unknown', 'mean':'unknown'}, 'weather':'unknown', 'date':target_date, 'location':location}



