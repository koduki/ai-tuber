from typing import Optional, List
from queue import Queue, Empty
import sys
import asyncio
import threading
import urllib.parse
import httpx

# --- I/O Abstraction ---
class IOAdapter:
    def __init__(self):
        self._input_queue = Queue()

    def write_output(self, text: str):
        print(text)

    def add_input(self, text: str):
        self._input_queue.put(text)

    def get_inputs(self) -> List[str]:
        inputs = []
        while not self._input_queue.empty():
            try:
                inputs.append(self._input_queue.get_nowait())
            except Empty:
                break
        return inputs

io_adapter = IOAdapter()

def stdin_reader():
    """Reads lines from stdin and puts them in a queue."""
    sys.stderr.write("DEBUG: Starting stdin_reader thread\n")
    while True:
        try:
            line = sys.stdin.readline()
            if line:
                io_adapter.add_input(line.strip())
        except Exception as e:
            sys.stderr.write(f"Error reading stdin: {e}\n")
            break

# Start stdin reader in background
threading.Thread(target=stdin_reader, daemon=True).start()

# --- Tool Implementations ---

async def speak(text: str, style: Optional[str] = None, **kwargs):
    """Speak the given text with an optional style."""
    style_str = f" ({style})" if style else ""
    io_adapter.write_output(f"\n[AI{style_str}]: {text}")
    return "Speaking completed"

async def change_emotion(emotion: str):
    """Change the visual emotion."""
    io_adapter.write_output(f"\n[Expression]: {emotion}")
    return "Emotion changed"

async def get_comments():
    """Get comments from the adapter."""
    inputs = io_adapter.get_inputs()
    if not inputs:
        return "No new comments."
    return "\n".join(inputs)

async def get_weather(location: str, date: Optional[str] = None):
    """
    Get weather for the specified location and date.

    Args:
        location: City name or location
        date: 'today', 'tomorrow', 'YYYY-MM-DD', or None (defaults to current)
    """
    # Use JSON format to get more details and forecast data
    encoded_location = urllib.parse.quote(location)
    url = f"https://wttr.in/{encoded_location}?format=j1"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            # Helper to format weather condition from hourly data
            def get_day_condition(hourly_data):
                # Using 12:00 PM (noon) as representative, or most frequent?
                # Index 4 corresponds to 1200 (noon) usually.
                try:
                    return hourly_data[4]['weatherDesc'][0]['value']
                except (IndexError, KeyError):
                    return "Unknown"

            # 1. No date specified -> Return current condition + Today's forecast
            if not date:
                current = data.get('current_condition', [{}])[0]
                temp = current.get('temp_C', 'N/A')
                desc = current.get('weatherDesc', [{}])[0].get('value', 'N/A')

                # Also get today's forecast
                today = data.get('weather', [{}])[0]
                max_temp = today.get('maxtempC', 'N/A')
                min_temp = today.get('mintempC', 'N/A')

                return (f"Current weather in {location}: {desc}, {temp}°C.\n"
                        f"Today's forecast: Max {max_temp}°C, Min {min_temp}°C.")

            # 2. Date specified
            target_date_index = -1

            # Map relative terms to indices
            if date.lower() == 'today':
                target_date_index = 0
            elif date.lower() == 'tomorrow':
                target_date_index = 1
            elif date.lower() in ['day after tomorrow', '2 days later']:
                target_date_index = 2

            weather_list = data.get('weather', [])

            # Try to match by date string if not relative
            if target_date_index == -1:
                for idx, day in enumerate(weather_list):
                    if day.get('date') == date:
                        target_date_index = idx
                        break

            if target_date_index != -1 and target_date_index < len(weather_list):
                day_data = weather_list[target_date_index]
                date_str = day_data.get('date')
                max_temp = day_data.get('maxtempC')
                min_temp = day_data.get('mintempC')
                condition = get_day_condition(day_data.get('hourly', []))

                return (f"Weather for {location} on {date_str}:\n"
                        f"Condition: {condition}\n"
                        f"Max Temp: {max_temp}°C\n"
                        f"Min Temp: {min_temp}°C")
            else:
                available_dates = [d.get('date') for d in weather_list]
                return (f"Forecast for date '{date}' not found. "
                        f"Available dates: {', '.join(available_dates)}")

    except Exception as e:
        return f"Failed to get weather for {location}: {str(e)}"
