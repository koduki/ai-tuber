import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from saint_graph.saint_graph import SaintGraph
from google.adk.runners import InMemoryRunner
from google.genai import types

@pytest.fixture
def mock_adk():
    with patch("saint_graph.saint_graph.Agent") as mock_agent, \
         patch("saint_graph.saint_graph.InMemoryRunner", spec=InMemoryRunner) as mock_runner, \
         patch("saint_graph.saint_graph.McpToolset") as mock_toolset:
        yield {
            "Agent": mock_agent,
            "InMemoryRunner": mock_runner,
            "McpToolset": mock_toolset
        }

@pytest.mark.asyncio
async def test_saint_graph_initialization(mock_adk):
    # Setup
    mcp_urls = ["http://localhost:8000"]
    system_instruction = "Test instruction"
    
    # Execute
    sg = SaintGraph(mcp_urls, system_instruction)
    
    # Verify
    assert sg.mcp_urls == mcp_urls
    assert sg.system_instruction == system_instruction
    mock_adk["McpToolset"].assert_called_once()
    mock_adk["Agent"].assert_called_once()
    mock_adk["InMemoryRunner"].assert_called_once_with(agent=sg.agent)

@pytest.mark.asyncio
async def test_process_turn_calls_runner(mock_adk):
    # Setup
    sg = SaintGraph(["http://localhost:8000"], "Instruction")
    
    # Simple MagicMock for run_async
    # autospec on unbound method causes trouble with 'self'
    mock_run_async = MagicMock()
    
    async def mock_iter(*args, **kwargs):
        yield "Event(name='speak')"

    mock_run_async.side_effect = mock_iter
    sg.runner.run_async = mock_run_async
    
    # Mock necessary attributes
    sg.runner.app_name = "TestApp"
    sg.runner.session_service = AsyncMock()
    sg.runner.session_service.get_session = AsyncMock(return_value="ExistingSession")
    
    # Execute
    await sg.process_turn("Hello")
    
    # Verify
    # ここでキーワード引数が使われていることを厳格にチェックする
    sg.runner.run_async.assert_called_with(
        new_message=types.Content(role="user", parts=[types.Part(text="Hello")]),
        user_id="yt_user",
        session_id="yt_session"
    )

@pytest.mark.asyncio
async def test_call_tool_traverses_toolsets(mock_adk):
    # Setup
    sg = SaintGraph(["http://localhost:8000"], "Instruction")
    
    mock_tool = AsyncMock()
    mock_tool.name = "sys_get_comments"
    mock_tool.run_async.return_value = "Result"
    
    mock_toolset = mock_adk["McpToolset"].return_value
    mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
    
    # Execute
    res = await sg.call_tool("sys_get_comments", {"arg": 1})
    
    # Verify
    assert res == "Result"
    # Note: we use tool_context=None in our simplified call_tool
    mock_tool.run_async.assert_called_once()
    args, kwargs = mock_tool.run_async.call_args
    assert kwargs["args"] == {"arg": 1}

@pytest.mark.asyncio
async def test_call_tool_not_found(mock_adk):
    # Setup
    sg = SaintGraph(["http://localhost:8000"], "Instruction")
    mock_toolset = mock_adk["McpToolset"].return_value
    mock_toolset.get_tools = AsyncMock(return_value=[])
    
    # Execute & Verify
    with pytest.raises(Exception, match="Tool unknown not found"):
        await sg.call_tool("unknown", {})
