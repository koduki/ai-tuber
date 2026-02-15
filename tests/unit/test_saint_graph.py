import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch
from saint_graph.saint_graph import SaintGraph
from google.adk.runners import InMemoryRunner
from google.genai import types

class MockEvent:
    def __init__(self, text):
        self.content = MagicMock()
        part = MagicMock()
        part.text = text
        self.content.parts = [part]
    def __str__(self):
        return "MockEvent"

@pytest.fixture
def mock_adk():
    with patch("saint_graph.saint_graph.Agent") as mock_agent, \
         patch("saint_graph.saint_graph.InMemoryRunner", spec=InMemoryRunner) as mock_runner, \
         patch("saint_graph.saint_graph.McpToolset") as mock_toolset, \
         patch("saint_graph.saint_graph.BodyClient") as mock_body_client, \
         patch("saint_graph.saint_graph.Event", MockEvent):
        yield {
            "Agent": mock_agent,
            "InMemoryRunner": mock_runner,
            "McpToolset": mock_toolset,
            "BodyClient": mock_body_client
        }

@pytest.mark.asyncio
async def test_saint_graph_initialization(mock_adk):
    # Setup
    mcp_url = "http://weather:8001/sse"
    system_instruction = "Test instruction"
    mock_body = mock_adk["BodyClient"]()
    
    # Execute
    sg = SaintGraph(mock_body, mcp_url, system_instruction)
    
    # Verify
    assert sg.system_instruction == system_instruction
    assert sg.body == mock_body
    mock_adk["McpToolset"].assert_called_once()
    mock_adk["Agent"].assert_called_once()
    mock_adk["InMemoryRunner"].assert_called_once_with(agent=sg.agent)

@pytest.mark.asyncio
async def test_process_turn_parses_emotion_tag(mock_adk):
    # Setup
    mock_body = mock_adk["BodyClient"]()
    sg = SaintGraph(mock_body, "", "Instruction")
    sg.body.change_emotion = AsyncMock()
    sg.body.speak = AsyncMock()
    
    mock_run_async = MagicMock()
    async def mock_iter(*args, **kwargs):
        yield MockEvent("[emotion: joyful] Hello World")

    mock_run_async.side_effect = mock_iter
    sg.runner.run_async = mock_run_async
    
    sg.runner.app_name = "TestApp"
    sg.runner.session_service = AsyncMock()
    sg.runner.session_service.get_session = AsyncMock(return_value="ExistingSession")
    
    # Execute
    await sg.process_turn("Hello")
    
    # Verify
    sg.body.change_emotion.assert_called_once_with("joyful")
    sg.body.speak.assert_called_once_with("Hello World", style="joyful", speaker_id=None)

@pytest.mark.asyncio
async def test_process_turn_defaults_to_neutral(mock_adk):
    # Setup
    mock_body = mock_adk["BodyClient"]()
    sg = SaintGraph(mock_body, "", "Instruction")
    sg.body.change_emotion = AsyncMock()
    sg.body.speak = AsyncMock()
    
    mock_run_async = MagicMock()
    async def mock_iter(*args, **kwargs):
        yield MockEvent("No tag here")

    mock_run_async.side_effect = mock_iter
    sg.runner.run_async = mock_run_async
    
    sg.runner.app_name = "TestApp"
    sg.runner.session_service = AsyncMock()
    sg.runner.session_service.get_session = AsyncMock(return_value="ExistingSession")
    
    # Execute
    await sg.process_turn("Hello")
    
    # Verify
    sg.body.change_emotion.assert_called_once_with("neutral")
    sg.body.speak.assert_called_once_with("No tag here", style="neutral", speaker_id=None)

def test_config_priority(monkeypatch):
    from saint_graph.config import Config
    
    # Test 1: Defaults
    monkeypatch.delenv("WEATHER_MCP_URL", raising=False)
    monkeypatch.delenv("MCP_URL", raising=False)
    cfg = Config()
    assert cfg.mcp_url == "http://tools-weather:8001/sse"
    
    # Test 2: MCP_URL (Legacy)
    monkeypatch.setenv("MCP_URL", "http://legacy:8001/sse")
    cfg = Config()
    assert cfg.mcp_url == "http://legacy:8001/sse"
    
    # Test 3: WEATHER_MCP_URL (Priority)
    monkeypatch.setenv("WEATHER_MCP_URL", "http://priority:8001/sse")
    cfg = Config()
    assert cfg.mcp_url == "http://priority:8001/sse"

def test_config_cloud_run_fail_fast(monkeypatch):
    from saint_graph.config import Config
    import pytest
    
    # Simulate Cloud Run environment without required env
    monkeypatch.setenv("K_SERVICE", "test-service")
    monkeypatch.delenv("WEATHER_MCP_URL", raising=False)
    
    cfg = Config()
    with pytest.raises(SystemExit) as e:
        cfg.validate()
    assert e.value.code == 1
    
    # Now set it
    monkeypatch.setenv("WEATHER_MCP_URL", "http://ok/sse")
    cfg = Config()
    cfg.validate() # Should not raise
