import pytest
from body.cli.main import mcp
from body.cli.tools import io_adapter
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_tools_list():
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "speak" in tool_names
    assert "get_comments" in tool_names
    assert "change_emotion" in tool_names

@pytest.mark.asyncio
async def test_call_speak_tool():
    with patch.object(io_adapter, 'write_output') as mock_write:
        # FastMCP.call_tool returns a list of content objects or a string
        result = await mcp.call_tool("speak", {"text": "Hello Test", "style": "happy"})
        
        assert "Speaking completed" in str(result)
        mock_write.assert_called_once()
        args, _ = mock_write.call_args
        assert "Hello Test" in args[0]
        assert "happy" in args[0]

@pytest.mark.asyncio
async def test_call_get_comments_tool():
    io_adapter.add_input("Test comment 1")
    
    result = await mcp.call_tool("get_comments", {})
    assert "Test comment 1" in str(result)
    
    # Second call should be empty
    result2 = await mcp.call_tool("get_comments", {})
    assert "No new comments." in str(result2)

@pytest.mark.asyncio
async def test_call_change_emotion():
    result = await mcp.call_tool("change_emotion", {"emotion": "angry"})
    assert "Emotion changed" in str(result)
