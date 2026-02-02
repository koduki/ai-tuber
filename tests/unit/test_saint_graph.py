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
         patch("google.adk.events.event.Event", MockEvent):
        yield {
            "Agent": mock_agent,
            "InMemoryRunner": mock_runner,
            "McpToolset": mock_toolset,
            "BodyClient": mock_body_client
        }

@pytest.mark.asyncio
async def test_saint_graph_initialization(mock_adk):
    # Setup
    body_url = "http://body-cli:8000"
    mcp_urls = ["http://weather:8001/sse"]
    system_instruction = "Test instruction"
    
    # Execute
    sg = SaintGraph(body_url, mcp_urls, system_instruction)
    
    # Verify
    assert sg.system_instruction == system_instruction
    mock_adk["BodyClient"].assert_called_once_with(base_url=body_url)
    mock_adk["McpToolset"].assert_called_once()
    mock_adk["Agent"].assert_called_once()
    mock_adk["InMemoryRunner"].assert_called_once_with(agent=sg.agent)

@pytest.mark.asyncio
async def test_process_turn_parses_emotion_tag(mock_adk):
    # Setup
    body_url = "http://body-cli:8000"
    sg = SaintGraph(body_url, [], "Instruction")
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
    sg.body.speak.assert_called_once_with("Hello World", style="joyful")

@pytest.mark.asyncio
async def test_process_turn_defaults_to_neutral(mock_adk):
    # Setup
    body_url = "http://body-cli:8000"
    sg = SaintGraph(body_url, [], "Instruction")
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
    sg.body.speak.assert_called_once_with("No tag here", style="neutral")
