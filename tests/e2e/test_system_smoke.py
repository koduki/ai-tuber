import pytest
import asyncio
import httpx
import os

# This test requires the services to be running (e.g. via docker-compose up)
# Since we cannot easily run docker-compose in this environment, 
# we provide this as a template for local/CI testing.

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_mcp_body_status(docker_ip, docker_services):
    """docker-composeで起動したMCP Bodyサーバーが正常に動作しているか確認。"""
    # docker_services.wait_until_responsive は同期Callableを期待する
    port = docker_services.port_for("body-cli", 8000)
    url = f"http://{docker_ip}:{port}/health"
    print(f"\nDEBUG: Checking MCP Body health at {url}")
    
    def check():
        try:
            import httpx
            with httpx.Client() as client:
                resp = client.get(url)
                return resp.status_code == 200
        except Exception as e:
            return False

    # サービスが立ち上がるまで最長90秒待機 (Buildに時間がかかる場合があるため)
    docker_services.wait_until_responsive(
        timeout=90.0, pause=2.0, check=check
    )
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_comment_cycle_e2e(docker_ip, docker_services):
    """
    外部からコメントが届き、ツールを介して取得できる一連の流れをテスト。
    """
    from google.adk.tools import McpToolset
    from google.adk.tools.mcp_tool.mcp_toolset import SseConnectionParams

    port = docker_services.port_for("body-cli", 8000)
    url = f"http://{docker_ip}:{port}/sse"
    
    # Use ADK's McpToolset to handle SSE/Session/JSON-RPC
    connection_params = SseConnectionParams(url=url)
    toolset = McpToolset(connection_params=connection_params)
    
    try:
        # 1. ツールリストを取得して、sys_get_commentsが存在するか確認
        tools = await toolset.get_tools()
        tool_names = [t.name for t in tools]
        assert "sys_get_comments" in tool_names
        
        # 2. ツールを叩いて「現在のコメント」を確認
        # Find the tool
        get_comments_tool = next(t for t in tools if t.name == "sys_get_comments")
        
        # Call it
        res = await get_comments_tool.run_async(args={}, tool_context=None)
        
        # FastMCP returns content blocks
        assert "No new comments." in str(res)
    finally:
        await toolset.close()
