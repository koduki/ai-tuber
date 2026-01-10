import pytest
import respx
import asyncio
from httpx import Response
from saint_graph.mcp_client import MCPClient

@pytest.mark.asyncio
async def test_call_tool_rpc_format():
    client = MCPClient(base_urls="http://testserver/sse")
    
    with respx.mock:
        # Mock SSE Handshake
        respx.get("http://testserver/sse").mock(return_value=Response(200, text="data: connected\n\n"))
        # Mock Initialize
        respx.post("http://testserver/messages").mock(return_value=Response(200, json={"jsonrpc": "2.0", "result": {"protocolVersion": "1.0", "capabilities": {}}, "id": 1}))
        
        await client.connect()
        
        if not client.clients:
            pytest.fail("Clients list is empty")
        
        target_client = client.clients[0]
        # We might need to force the post_url if connect detection failed or was simplified
        target_client.post_url = "http://testserver/messages"
        
        # Define mock response for tool call
        route = respx.post("http://testserver/messages").mock(return_value=Response(200, json={
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": "I am speaking"}]
            },
            "id": 1
        }))
        
        # We need to manually populate tool_map for this test if list_tools wasn't called
        client.tool_map = {"speak": target_client}
        
        result = await client.call_tool("speak", {"text": "hello"})
        
        # Verify request
        assert route.called
        import json
        request_data = json.loads(route.calls.last.request.content)
        assert request_data["method"] == "tools/call"
        assert request_data["params"]["name"] == "speak"

        # Verify result
        assert result == "I am speaking"

@pytest.mark.asyncio
async def test_call_tool_error_handling():
    client = MCPClient(base_urls="http://testserver/sse")
    
    with respx.mock:
        respx.get("http://testserver/sse").mock(return_value=Response(200, text="data: connected\n\n"))
        respx.post("http://testserver/messages").mock(return_value=Response(200, json={"jsonrpc": "2.0", "result": {"protocolVersion": "1.0"}, "id": 1}))
        
        await client.connect()
        target_client = client.clients[0]
        target_client.post_url = "http://testserver/messages"
        client.tool_map = {"non_existent": target_client}
        
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
    client = MCPClient(base_urls=["http://testserver/sse"])
    
    with respx.mock:
        respx.get("http://testserver/sse").mock(return_value=Response(200, text="data: connected\n\n"))
        respx.post("http://testserver/messages").mock(return_value=Response(200, json={"jsonrpc": "2.0", "result": {"protocolVersion": "1.0"}, "id": 1}))
        
        await client.connect()
        target_client = client.clients[0]
        target_client.post_url = "http://testserver/messages"
        
        respx.post("http://testserver/messages").mock(return_value=Response(200, json={
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {"name": "test_tool", "description": "A test tool", "inputSchema": {"type": "object"}}
                ]
            },
            "id": 1
        }))
        
        tools = await target_client.list_tools()
        
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert target_client.tools == tools
