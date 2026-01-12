from typing import Optional
import urllib.request
import urllib.parse
import json
import traceback
from datetime import datetime

async def get_weather(location: str, date: Optional[str] = None):
    """
    Open-Meteo APIを使用して、指定された場所と日付の天気を取得します。
    """
    print(f"DEBUG: get_weather called for location='{location}', date='{date}'")
    headers = {'User-Agent': 'SaintGraphWeather/1.0'}
    try:
        # 1. ジオコーディング（地名から緯度経度を取得）
        encoded_loc = urllib.parse.quote(location)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=1&language=ja&format=json"
        
        req = urllib.request.Request(geo_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            geo_data = json.loads(res.read().decode())
        
        if not geo_data.get('results'):
            return f"'{location}' という場所は見つかりませんでした。"
            
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        resolved_name = geo_data['results'][0]['name']

        # 2. 天気データの取得
        weather_url = (f"https://api.open-meteo.com/v1/forecast?"
                       f"latitude={lat}&longitude={lon}&current_weather=true&"
                       f"daily=weathercode,temperature_2m_max,temperature_2m_min&"
                       f"timezone=auto")
        
        req = urllib.request.Request(weather_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            w_data = json.loads(res.read().decode())

        # WMO天気コードからテキスト説明への変換ヘルパー
        def get_wmo_desc(code):
            mapping = {
                0: "晴天",
                1: "快晴", 2: "晴れ", 3: "くもり",
                45: "霧", 48: "霧（氷結性）",
                51: "霧雨（弱）", 53: "霧雨（並）", 55: "霧雨（強）",
                61: "雨（弱）", 63: "雨（並）", 65: "雨（強）",
                71: "雪（弱）", 73: "雪（並）", 75: "雪（強）",
                95: "雷雨",
            }
            return mapping.get(code, f"不明（コード:{code}）")

        # 3. 日付の解析とデータ抽出
        today_str = datetime.now().strftime('%Y-%m-%d')
        target_idx = -1 
        
        if not date or date.lower() == 'today':
            target_idx = 0
        elif date.lower() == 'tomorrow':
            target_idx = 1
        elif date.lower() in ['day after tomorrow', '2 days later']:
            target_idx = 2
        else:
            times = w_data['daily']['time']
            if date in times:
                target_idx = times.index(date)
            else:
                 available = times[:3]
                 return f"{date} の予報は利用できません。取得可能な範囲: {', '.join(available)}..."

        res_strings = []
        res_strings.append(f"{resolved_name} の天気（参照元: Open-Meteo）:")

        # 現在の天気を追加（日付指定がない場合のみ）
        if not date:
            curr = w_data.get('current_weather', {})
            temp = curr.get('temperature')
            code = curr.get('weathercode')
            desc = get_wmo_desc(code)
            res_strings.append(f"現在: {desc}, 気温 {temp}°C")

        # 予報データの抽出
        if target_idx != -1 and target_idx < len(w_data['daily']['time']):
            day_date = w_data['daily']['time'][target_idx]
            d_max = w_data['daily']['temperature_2m_max'][target_idx]
            d_min = w_data['daily']['temperature_2m_min'][target_idx]
            d_desc = get_wmo_desc(w_data['daily']['weathercode'][target_idx])
            
            label = "今日の予報" if target_idx == 0 else f"{day_date} の予報"
            res_strings.append(f"{label}: {d_desc}, 最高 {d_max}°C, 最低 {d_min}°C")
        
        return "\n".join(res_strings)

    except Exception:
        t = traceback.format_exc()
        print(f"Weather Error: {t}")
        return f"{location} の天気取得に失敗しました。エラー: {t.splitlines()[-1]}"
