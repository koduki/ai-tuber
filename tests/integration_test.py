# import pytest
# import os
# from unittest.mock import MagicMock, patch, AsyncMock
# from saint_graph.saint_graph import SaintGraph
# from google.adk.models import Gemini
# from google.adk import Agent
# from google.adk.runners import InMemoryRunner

# @pytest.mark.asyncio
# async def test_weather_scenario(monkeypatch):
#     # 1. 環境設定
#     # APIキーは環境変数から読み込む
#     api_key = os.getenv("GOOGLE_API_KEY")
#     if not api_key:
#         pytest.skip("GOOGLE_API_KEY not set")

#     # ツール呼び出し順序記録用
#     tool_call_log = []

#     # モックツールを作成
#     # speakツール
#     speak_args = []
#     async def mock_speak(text: str, style: str = None):
#         tool_call_log.append("speak")
#         speak_args.append({"text": text, "style": style})
#         return "Speaking completed"

#     # get_weatherツール
#     async def mock_get_weather(city: str):
#         tool_call_log.append("get_weather")
#         return f"{city} is sunny today."

#     # ADKのTool形式にラップ
#     try:
#         from google.adk.tools import FunctionTool
#     except ImportError:
#         pytest.fail("google.adk.tools.FunctionTool not found")

#     tool_speak = FunctionTool(mock_speak, name="speak", description="Speak text to the user.")
#     tool_weather = FunctionTool(mock_get_weather, name="get_weather", description="Get weather info.")

#     # 2. SaintGraphの初期化（McpToolsetをモック化）
#     with patch("saint_graph.saint_graph.McpToolset") as MockToolsetClass:
#         mock_instance = MockToolsetClass.return_value
#         mock_instance.close = AsyncMock()

#         sg = SaintGraph(mcp_urls=["http://dummy"], system_instruction="You are a helpful assistant.")

#         # 3. Agentのtoolsを差し替え
#         sg.agent.tools = [tool_speak, tool_weather]
#         sg.runner = InMemoryRunner(agent=sg.agent)

#         # Persona読み込み（ファイルを直接読み込む）
#         base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
#         persona_path = os.path.join(base_dir, "mind", "ren", "persona.md")
#         core_path = os.path.join(base_dir, "saint_graph", "core_instructions.md")

#         instruction = ""
#         if os.path.exists(core_path):
#             with open(core_path, "r", encoding="utf-8") as f:
#                 instruction += f.read() + "\n\n"
#         if os.path.exists(persona_path):
#             with open(persona_path, "r", encoding="utf-8") as f:
#                 instruction += f.read()

#         if instruction:
#             sg.agent.instruction = instruction

#         # 4. テスト実行
#         print("Sending query to Gemini...")
#         await sg.process_turn("今日の福岡の天気は？")

#         # 5. 検証
#         # 順序検証: get_weather -> speak
#         print(f"Tool call log: {tool_call_log}")
#         assert "get_weather" in tool_call_log, "get_weather should be called"
#         assert "speak" in tool_call_log, "speak should be called"

#         # get_weatherがspeakより先に呼ばれていること
#         assert tool_call_log.index("get_weather") < tool_call_log.index("speak"), "get_weather must be called before speak"

#         # speakの内容検証
#         last_speak = speak_args[-1]
#         assert "晴" in last_speak["text"] or "sunny" in last_speak["text"].lower()
