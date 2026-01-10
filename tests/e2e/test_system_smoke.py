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
    port = docker_services.port_for("body-cli", 8000)
    base_url = f"http://{docker_ip}:{port}"

    # 1. ツールリストを取得して、get_commentsが存在するか確認
    rpc_list_payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
    }

    async with httpx.AsyncClient() as client:
        # 初回のリクエストは自動待機後のため通るはず
        resp = await client.post(f"{base_url}/messages?session_id=test", json=rpc_list_payload)
        assert resp.status_code == 200
        data = resp.json()
        tools = [t["name"] for t in data["result"]["tools"]]
        assert "get_comments" in tools

    # 2. ツールを叩いて「現在のコメント」を確認
    rpc_call_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_comments",
            "arguments": {}
        },
        "id": 2
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/messages?session_id=test", json=rpc_call_payload)
        assert resp.status_code == 200
        assert "No new comments." in resp.text
