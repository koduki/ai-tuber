import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from saint_graph.saint_graph import SaintGraph

@pytest.fixture
def mock_adk():
    with patch("saint_graph.saint_graph.Agent") as mock_agent, \
         patch("saint_graph.saint_graph.InMemoryRunner") as mock_runner, \
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
    sg.runner.run_debug = AsyncMock()
    
    # Execute
    await sg.process_turn("Hello")
    
    # Verify
    sg.runner.run_debug.assert_called_once_with(
        "Hello",
        user_id="yt_user",
        session_id="yt_session",
        verbose=True
    )

@pytest.mark.asyncio
async def test_call_tool_traverses_toolsets(mock_adk):
    # Setup
    sg = SaintGraph(["http://localhost:8000"], "Instruction")
    
    mock_tool = AsyncMock()
    mock_tool.name = "get_comments"
    mock_tool.run_async.return_value = "Result"
    
    mock_toolset = mock_adk["McpToolset"].return_value
    mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
    
    # Execute
    res = await sg.call_tool("get_comments", {"arg": 1})
    
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
