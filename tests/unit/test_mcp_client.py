import pytest
import respx
from httpx import Response
from saint_graph.mcp_client import MCPClient

@pytest.mark.asyncio
async def test_call_tool_rpc_format():
    client = MCPClient(base_url="http://testserver/sse")
    client.post_url = "http://testserver/messages"
    
    with respx.mock:
        # Define mock response
        route = respx.post("http://testserver/messages").mock(return_value=Response(200, json={
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": "I am speaking"}]
            },
            "id": 1
        }))
        
        result = await client.call_tool("speak", {"text": "hello"})
        
        # Verify request
        assert route.called
        import json
        request_data = json.loads(route.calls.last.request.content)
        assert request_data["method"] == "tools/call"
        assert request_data["params"]["name"] == "speak"
        assert request_data["params"]["arguments"] == {"text": "hello"}
        
        # Verify result
        assert result == "I am speaking"

@pytest.mark.asyncio
async def test_call_tool_error_handling():
    client = MCPClient(base_url="http://testserver/sse")
    client.post_url = "http://testserver/messages"
    
    with respx.mock:
        respx.post("http://testserver/messages").mock(return_value=Response(200, json={
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": "Method not found"},
            "id": 1
        }))
        
        with pytest.raises(Exception) as excinfo:
            await client.call_tool("non_existent", {})
        
        assert "Tool Error" in str(excinfo.value)
        assert "Method not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_tools_parsing():
    client = MCPClient(base_url="http://testserver/sse")
    client.post_url = "http://testserver/messages"
    
    with respx.mock:
        respx.post("http://testserver/messages").mock(return_value=Response(200, json={
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {"name": "test_tool", "description": "A test tool", "inputSchema": {"type": "object"}}
                ]
            },
            "id": 1
        }))
        
        tools = await client.list_tools()
        
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert client.tools == tools
