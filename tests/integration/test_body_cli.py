import pytest
from fastapi.testclient import TestClient
from body.cli.main import app, io_adapter
from unittest.mock import patch

@pytest.fixture
def client():
    return TestClient(app)

def test_tools_list(client):
    response = client.post("/messages", json={
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    tool_names = [t["name"] for t in data["result"]["tools"]]
    assert "speak" in tool_names
    assert "get_comments" in tool_names

def test_call_speak_tool(client):
    # Reset or clear io_adapter if possible, but here we can just check if it was called
    with patch.object(io_adapter, 'write_output') as mock_write:
        response = client.post("/messages", json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "speak",
                "arguments": {"text": "Hello Test", "style": "happy"}
            },
            "id": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["content"][0]["text"] == "Speaking completed"
        
        # Verify output
        mock_write.assert_called_once()
        args, _ = mock_write.call_args
        assert "Hello Test" in args[0]
        assert "happy" in args[0]

def test_call_get_comments_tool(client):
    # Add some input to adapter
    io_adapter.add_input("Test comment 1")
    io_adapter.add_input("Test comment 2")
    
    response = client.post("/messages", json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_comments",
            "arguments": {}
        },
        "id": 3
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "Test comment 1" in data["result"]["content"][0]["text"]
    assert "Test comment 2" in data["result"]["content"][0]["text"]
    
    # Second call should be empty
    response = client.post("/messages", json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_comments",
            "arguments": {}
        },
        "id": 4
    })
    assert "No new comments." in response.json()["result"]["content"][0]["text"]

def test_invalid_method(client):
    response = client.post("/messages", json={
        "jsonrpc": "2.0",
        "method": "non_existent",
        "id": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32601
