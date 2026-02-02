import pytest
import asyncio
import httpx
import os

def is_service_running():
    """Check if MCP service is already running on localhost:8000"""
    try:
        with httpx.Client() as client:
            resp = client.get("http://localhost:8000/health", timeout=2.0)
            return resp.status_code == 200
    except Exception:
        return False

@pytest.mark.e2e
@pytest.mark.skipif(not is_service_running(), reason="MCP service not running on localhost:8000. Start with 'docker compose up' first.")
@pytest.mark.asyncio
async def test_mcp_body_status():
    """docker-composeで起動したMCP Bodyサーバーが正常に動作しているか確認。"""
    url = "http://localhost:8000/health"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

@pytest.mark.e2e
@pytest.mark.skipif(not is_service_running(), reason="MCP service not running on localhost:8000. Start with 'docker compose up' first.")
@pytest.mark.asyncio
async def test_comment_cycle_e2e():
    """
    外部からコメントが届き、ツールを介して取得できる一連の流れをテスト。
    """
    from google.adk.tools import McpToolset
    from google.adk.tools.mcp_tool.mcp_toolset import SseConnectionParams

    url = "http://localhost:8000/sse"
    
    # Use ADK's McpToolset to handle SSE/Session/JSON-RPC
    connection_params = SseConnectionParams(url=url)
    toolset = McpToolset(connection_params=connection_params)
    
    try:
        # 1. ツールリストを取得して、sys_get_commentsが存在するか確認
        tools = await toolset.get_tools()
        tool_names = [t.name for t in tools]
        assert "sys_get_comments" in tool_names
        
        # 2. ツールを叩いて「現在のコメント」を確認
        get_comments_tool = next(t for t in tools if t.name == "sys_get_comments")
        
        # Call it
        res = await get_comments_tool.run_async(args={}, tool_context=None)
        
        # FastMCP returns content blocks
        assert "No new comments." in str(res)
    finally:
        await toolset.close()
