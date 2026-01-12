from typing import Optional
import urllib.request
import urllib.parse
import json
import traceback
from datetime import datetime

# --- WMOコード定数 ---
WMO_CODE_MAP = {
    0: "晴天",
    1: "快晴", 2: "晴れ", 3: "くもり",
    45: "霧", 48: "霧（氷結性）",
    51: "霧雨（弱）", 53: "霧雨（並）", 55: "霧雨（強）",
    61: "雨（弱）", 63: "雨（並）", 65: "雨（強）",
    71: "雪（弱）", 73: "雪（並）", 75: "雪（強）",
    95: "雷雨",
}

def get_wmo_description(code: int) -> str:
    """WMO天気コードを日本語の説明に変換します。"""
    return WMO_CODE_MAP.get(code, f"不明（コード:{code}）")


# --- 日付解析 ---
def _parse_target_date_index(date: Optional[str], available_times: list[str]) -> int:
    """
    日付文字列を予報データのインデックスに変換します。
    見つからない場合は -1 を返します。
    """
    if not date or date.lower() == 'today':
        return 0
    elif date.lower() == 'tomorrow':
        return 1
    elif date.lower() in ['day after tomorrow', '2 days later']:
        return 2
    elif date in available_times:
        return available_times.index(date)
    return -1


# --- メインAPI ---
async def get_weather(location: str, date: Optional[str] = None) -> str:
    """
    Open-Meteo APIを使用して、指定された場所と日付の天気を取得します。
    """
    print(f"DEBUG: get_weather called for location='{location}', date='{date}'")
    headers = {'User-Agent': 'SaintGraphWeather/1.0'}
    
    try:
        # ジオコーディング（地名から緯度経度を取得）
        lat, lon, resolved_name = await _geocode(location, headers)
        if lat is None:
            return f"'{location}' という場所は見つかりませんでした。"

        # 天気データの取得
        weather_data = await _fetch_weather(lat, lon, headers)

        # レスポンスの構築
        return _format_weather_response(resolved_name, weather_data, date)

    except Exception:
        t = traceback.format_exc()
        print(f"Weather Error: {t}")
        return f"{location} の天気取得に失敗しました。エラー: {t.splitlines()[-1]}"


# --- ヘルパー関数 ---

async def _geocode(location: str, headers: dict) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """地名から緯度経度を取得します。"""
    encoded_loc = urllib.parse.quote(location)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=1&language=ja&format=json"
    
    req = urllib.request.Request(geo_url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        geo_data = json.loads(res.read().decode())
    
    if not geo_data.get('results'):
        return None, None, None
        
    result = geo_data['results'][0]
    return result['latitude'], result['longitude'], result['name']


async def _fetch_weather(lat: float, lon: float, headers: dict) -> dict:
    """Open-Meteo APIから天気データを取得します。"""
    weather_url = (f"https://api.open-meteo.com/v1/forecast?"
                   f"latitude={lat}&longitude={lon}&current_weather=true&"
                   f"daily=weathercode,temperature_2m_max,temperature_2m_min&"
                   f"timezone=auto")
    
    req = urllib.request.Request(weather_url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode())


def _format_weather_response(resolved_name: str, w_data: dict, date: Optional[str]) -> str:
    """天気データを読みやすい文字列にフォーマットします。"""
    res_strings = [f"{resolved_name} の天気（参照元: Open-Meteo）:"]

    # 現在の天気（日付指定がない場合のみ）
    if not date:
        curr = w_data.get('current_weather', {})
        temp = curr.get('temperature')
        desc = get_wmo_description(curr.get('weathercode'))
        res_strings.append(f"現在: {desc}, 気温 {temp}°C")

    # 予報データ
    times = w_data['daily']['time']
    target_idx = _parse_target_date_index(date, times)
    
    if target_idx == -1 and date:
        available = times[:3]
        return f"{date} の予報は利用できません。取得可能な範囲: {', '.join(available)}..."

    if target_idx != -1 and target_idx < len(times):
        day_date = times[target_idx]
        d_max = w_data['daily']['temperature_2m_max'][target_idx]
        d_min = w_data['daily']['temperature_2m_min'][target_idx]
        d_desc = get_wmo_description(w_data['daily']['weathercode'][target_idx])
        
        label = "今日の予報" if target_idx == 0 else f"{day_date} の予報"
        res_strings.append(f"{label}: {d_desc}, 最高 {d_max}°C, 最低 {d_min}°C")
    
    return "\n".join(res_strings)
