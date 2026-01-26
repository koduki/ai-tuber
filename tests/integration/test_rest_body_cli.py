import pytest
from body.cli.main import app
from body.cli.tools import io_adapter
from unittest.mock import patch
from starlette.testclient import TestClient

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_speak_api():
    with patch("body.cli.main.speak") as mock_speak:
        mock_speak.return_value = "Speaking completed"
        response = client.post("/api/speak", json={"text": "Hello Test", "style": "happy"})
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["result"] == "Speaking completed"
        mock_speak.assert_called_once_with("Hello Test", "happy")

def test_change_emotion_api():
    with patch("body.cli.main.change_emotion") as mock_change:
        mock_change.return_value = "Emotion changed to angry"
        response = client.post("/api/change_emotion", json={"emotion": "angry"})
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["result"] == "Emotion changed to angry"
        mock_change.assert_called_once_with("angry")

def test_get_comments_api():
    with patch("body.cli.main.get_comments") as mock_get:
        mock_get.return_value = "Test comment 1\nTest comment 2"
        response = client.get("/api/comments")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["comments"] == ["Test comment 1", "Test comment 2"]
        mock_get.assert_called_once()

def test_get_comments_empty_api():
    with patch("body.cli.main.get_comments") as mock_get:
        mock_get.return_value = "No new comments."
        response = client.get("/api/comments")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["comments"] == []
        mock_get.assert_called_once()
