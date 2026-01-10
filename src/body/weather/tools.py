from typing import Optional
import urllib.request
import urllib.parse
import json
import traceback
from datetime import datetime, timedelta

async def get_weather(location: str, date: Optional[str] = None):
    """
    Get weather for the specified location and date using Open-Meteo API.
    """
    print(f"DEBUG: get_weather called for location='{location}', date='{date}'")
    headers = {'User-Agent': 'SaintGraphWeather/1.0'}
    try:
        # 1. Geocoding
        encoded_loc = urllib.parse.quote(location)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=1&language=ja&format=json"
        
        req = urllib.request.Request(geo_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            geo_data = json.loads(res.read().decode())
        
        if not geo_data.get('results'):
            return f"Location '{location}' not found."
            
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        resolved_name = geo_data['results'][0]['name']

        # 2. Weather Fetch
        weather_url = (f"https://api.open-meteo.com/v1/forecast?"
                       f"latitude={lat}&longitude={lon}&current_weather=true&"
                       f"daily=weathercode,temperature_2m_max,temperature_2m_min&"
                       f"timezone=auto")
        
        req = urllib.request.Request(weather_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            w_data = json.loads(res.read().decode())

        # Helper: WMO Code to String
        def get_wmo_desc(code):
            mapping = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Drizzle: Light", 53: "Drizzle: Moderate", 55: "Drizzle: Dense intensity",
                61: "Rain: Slight", 63: "Rain: Moderate", 65: "Rain: Heavy intensity",
                71: "Snow fall: Slight", 73: "Snow fall: Moderate", 75: "Snow fall: Heavy intensity",
                95: "Thunderstorm",
            }
            return mapping.get(code, f"Unknown code {code}")

        # 3. Parse Logic
        today_str = datetime.now().strftime('%Y-%m-%d')
        target_idx = -1 
        
        if not date or date.lower() == 'today':
            target_idx = 0
            target_date_str = today_str
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
                 return f"Forecast for {date} not available. Available: {', '.join(available)}..."

        res_strings = []
        res_strings.append(f"Weather for {resolved_name} (Source: Open-Meteo):")

        if not date:
            curr = w_data.get('current_weather', {})
            temp = curr.get('temperature')
            code = curr.get('weathercode')
            desc = get_wmo_desc(code)
            res_strings.append(f"Current: {desc}, {temp}°C")

        if target_idx != -1 and target_idx < len(w_data['daily']['time']):
            day_date = w_data['daily']['time'][target_idx]
            d_max = w_data['daily']['temperature_2m_max'][target_idx]
            d_min = w_data['daily']['temperature_2m_min'][target_idx]
            d_desc = get_wmo_desc(w_data['daily']['weathercode'][target_idx])
            
            label = "Today's forecast" if target_idx == 0 else f"Forecast for {day_date}"
            res_strings.append(f"{label}: {d_desc}, Max {d_max}°C, Min {d_min}°C")
        
        return "\n".join(res_strings)

    except Exception:
        t = traceback.format_exc()
        print(f"Weather Error: {t}")
        return f"Failed to get weather for {location}. Error: {t.splitlines()[-1]}"
