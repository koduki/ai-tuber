
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from google.adk.tools.function_tool import FunctionTool
from google.genai import types
from saint_graph.saint_graph import SaintGraph
from saint_graph.prompt_loader import PromptLoader
from saint_graph.telemetry import setup_telemetry

# Skip tests in GitHub Actions environment
@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", reason="Skipping integration test in GitHub Actions due to missing secrets")
@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="GOOGLE_API_KEY not set")
@pytest.mark.asyncio
async def test_weather_scenario():
    """
    Integration test validating the cycle of User Input -> Weather Tool -> Speak Tool.
    Uses mock tools but real LLM (Gemini).

    NOTE: This test is subject to LLM non-determinism. The LLM may sometimes choose
    to ask clarifying questions instead of immediately calling the weather tool.
    We verify that at least the speak tool is used for communication.

    Execution:
        GOOGLE_API_KEY=your_key pytest tests/integration/test_agent_scenarios.py
    """
    setup_telemetry()
    
    # 1. Setup Mock Tools
    speak_calls = []
    weather_calls = []
    emotion_calls = []

    def get_weather(location: str, date: str = "today") -> str:
        """Retrieve weather information for a specified location and date.
        
        Args:
            location: The location to get weather for (e.g., "福岡", "Tokyo")
            date: The date to get weather for. Defaults to "today" if not specified.
        
        Returns:
            Weather information as a string.
        """
        print(f"\n[Mock Tool] get_weather called for {location}, date={date}")
        weather_calls.append({"location": location, "date": date})
        return f"{location}の天気は晴れです。気温は20度です。"

    def speak(text: str, style: str = None, **kwargs) -> str:
        """Speak text to the audience."""
        print(f"\n[Mock Tool] speak called: {text} (style={style}, kwargs={kwargs})")
        speak_calls.append({"text": text, "style": style})
        return "Speaking completed"

    def change_emotion(emotion: str) -> str:
        """Change the avatar's facial expression."""
        print(f"\n[Mock Tool] change_emotion called: {emotion}")
        emotion_calls.append(emotion)
        return "Emotion changed"

    # Wrap python functions as ADK tools
    weather_tool = FunctionTool(get_weather)
    speak_tool = FunctionTool(speak)
    change_emotion_tool = FunctionTool(change_emotion)
    
    # 2. Initialize SaintGraph with local tools
    loader = PromptLoader("ren")
    system_instruction = loader.load_system_instruction()
    
    with patch("saint_graph.saint_graph.BodyClient") as mock_body_class:
        mock_body_client = mock_body_class.return_value
        mock_body_client.speak = AsyncMock(side_effect=speak)
        mock_body_client.change_emotion = AsyncMock(side_effect=change_emotion)
        
        # Initialize SaintGraph with dummy body_url, empty mcp_urls and custom tools
        sg = SaintGraph(
            body_url="http://mock-body",
            mcp_urls=[], 
            system_instruction=system_instruction,
            tools=[weather_tool]
        )
    
    try:
        # 3. Execute Turn
        user_input = "福岡の今日の天気を教えて。"
        print(f"\n[User]: {user_input}")
        
        await sg.process_turn(user_input)
        
        # 4. Verify Results
        
        # CRITICAL VERIFICATION: speak must be called to communicate
        assert len(speak_calls) > 0, \
            f"""ERROR: 'speak' tool was not called! Agent did not respond with speech.
            
This is a critical failure - the agent must use the speak tool to communicate.
Tools called: get_weather={len(weather_calls)}, speak={len(speak_calls)}, change_emotion={len(emotion_calls)}

Debug info:
- Weather calls: {weather_calls}
- Speak calls: {speak_calls}
- Emotion calls: {emotion_calls}
"""
        
        print(f"✓ speak called {len(speak_calls)} time(s)")
        
        # INFORMATIONAL: Check if weather tool was used
        # Note: Due to LLM non-determinism, the weather tool may not always be called
        # in the first turn. The LLM might ask for clarification instead.
        if len(weather_calls) > 0:
            print(f"✓ get_weather called {len(weather_calls)} time(s) - Location: {weather_calls[0]['location']}")
        else:
            print(f"⚠ get_weather was not called (LLM chose to respond without fetching data)")
            print(f"  This is acceptable due to LLM non-determinism.")
            
        last_speech = speak_calls[-1]["text"]
        print(f"\n[Final AI Response]: {last_speech}")
        
        # Verify that the agent is responding in Japanese and using the character's voice
        assert any("じゃ" in call["text"] or "のう" in call["text"] or "わらわ" in call["text"] 
                   for call in speak_calls), \
            "Agent should respond using the character's speech pattern (e.g., じゃ, のう, わらわ)"
            
    finally:
        await sg.close()
