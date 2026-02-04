"""
Integration tests for speaker_id functionality.
Tests that speaker_id from mind.json is correctly passed through the entire system.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from saint_graph.saint_graph import SaintGraph
from saint_graph.prompt_loader import PromptLoader


class MockEvent:
    """Mock event for ADK runner that matches the expected structure"""
    def __init__(self, text):
        self.content = MagicMock()
        part = MagicMock()
        part.text = text
        self.content.parts = [part]


@pytest.mark.asyncio
@patch("saint_graph.saint_graph.Event", MockEvent)
async def test_speaker_id_passed_to_body_client():
    """mind_configのspeaker_idがBodyClient.speak()に渡される"""
    mind_config = {"speaker_id": 58}
    
    with patch("saint_graph.saint_graph.BodyClient") as mock_body_class:
        mock_body = mock_body_class.return_value
        mock_body.speak = AsyncMock()
        mock_body.change_emotion = AsyncMock()
        
        sg = SaintGraph(
            body_url="http://test",
            mcp_url="",
            system_instruction="Test instruction",
            mind_config=mind_config
        )
        
        # モックランナーのセットアップ
        mock_runner = MagicMock()
        
        async def mock_iter(*args, **kwargs):
            yield MockEvent("[emotion: neutral] Hello from test")
        
        mock_runner.run_async = MagicMock(side_effect=mock_iter)
        mock_runner.app_name = "TestApp"
        mock_runner.session_service = AsyncMock()
        mock_runner.session_service.get_session = AsyncMock(return_value=None)
        mock_runner.session_service.create_session = AsyncMock()
        sg.runner = mock_runner
        
        await sg.process_turn("test input")
        
        # speaker_id=58が渡されることを確認
        mock_body.speak.assert_called_once()
        call_args = mock_body.speak.call_args
        assert call_args.kwargs["speaker_id"] == 58
        assert call_args.args[0] == "Hello from test"
        assert call_args.kwargs["style"] == "neutral"


@pytest.mark.asyncio
@patch("saint_graph.saint_graph.Event", MockEvent)
async def test_no_speaker_id_defaults_to_none():
    """mind_configがない場合、speaker_id=Noneが渡される"""
    with patch("saint_graph.saint_graph.BodyClient") as mock_body_class:
        mock_body = mock_body_class.return_value
        mock_body.speak = AsyncMock()
        mock_body.change_emotion = AsyncMock()
        
        # mind_configなしでSaintGraphを初期化
        sg = SaintGraph(
            body_url="http://test",
            mcp_url="",
            system_instruction="Test instruction"
        )
        
        # モックランナーのセットアップ
        mock_runner = MagicMock()
        
        async def mock_iter(*args, **kwargs):
            yield MockEvent("[emotion: happy] Test response")
        
        mock_runner.run_async = MagicMock(side_effect=mock_iter)
        mock_runner.app_name = "TestApp"
        mock_runner.session_service = AsyncMock()
        mock_runner.session_service.get_session = AsyncMock(return_value=None)
        mock_runner.session_service.create_session = AsyncMock()
        sg.runner = mock_runner
        
        await sg.process_turn("test input")
        
        # speaker_id=Noneが渡されることを確認
        mock_body.speak.assert_called_once()
        call_args = mock_body.speak.call_args
        assert call_args.kwargs["speaker_id"] is None


@pytest.mark.asyncio
@patch("saint_graph.saint_graph.Event", MockEvent)
async def test_speaker_id_zero_is_valid():
    """speaker_id=0も有効な値として扱われる"""
    mind_config = {"speaker_id": 0}
    
    with patch("saint_graph.saint_graph.BodyClient") as mock_body_class:
        mock_body = mock_body_class.return_value
        mock_body.speak = AsyncMock()
        mock_body.change_emotion = AsyncMock()
        
        sg = SaintGraph(
            body_url="http://test",
            mcp_url="",
            system_instruction="Test instruction",
            mind_config=mind_config
        )
        
        # モックランナーのセットアップ
        mock_runner = MagicMock()
        
        async def mock_iter(*args, **kwargs):
            yield MockEvent("Test without emotion tag")
        
        mock_runner.run_async = MagicMock(side_effect=mock_iter)
        mock_runner.app_name = "TestApp"
        mock_runner.session_service = AsyncMock()
        mock_runner.session_service.get_session = AsyncMock(return_value=None)
        mock_runner.session_service.create_session = AsyncMock()
        sg.runner = mock_runner
        
        await sg.process_turn("test input")
        
        # speaker_id=0が渡されることを確認（Falsy値だがNoneではない）
        mock_body.speak.assert_called_once()
        call_args = mock_body.speak.call_args
        assert call_args.kwargs["speaker_id"] == 0


@pytest.mark.asyncio
@patch("saint_graph.saint_graph.Event", MockEvent)
async def test_multiple_sentences_use_same_speaker_id():
    """複数のセンテンスで同じspeaker_idが使われる"""
    mind_config = {"speaker_id": 42}
    
    with patch("saint_graph.saint_graph.BodyClient") as mock_body_class:
        mock_body = mock_body_class.return_value
        mock_body.speak = AsyncMock()
        mock_body.change_emotion = AsyncMock()
        
        sg = SaintGraph(
            body_url="http://test",
            mcp_url="",
            system_instruction="Test instruction",
            mind_config=mind_config
        )
        
        # モックランナーのセットアップ
        mock_runner = MagicMock()
        
        async def mock_iter(*args, **kwargs):
            yield MockEvent("[emotion: neutral] First sentence。[emotion: happy] Second sentence！")
        
        mock_runner.run_async = MagicMock(side_effect=mock_iter)
        mock_runner.app_name = "TestApp"
        mock_runner.session_service = AsyncMock()
        mock_runner.session_service.get_session = AsyncMock(return_value=None)
        mock_runner.session_service.create_session = AsyncMock()
        sg.runner = mock_runner
        
        await sg.process_turn("test input")
        
        # 両方のspeakコールでspeaker_id=42が使われる
        assert mock_body.speak.call_count == 2
        for call in mock_body.speak.call_args_list:
            assert call.kwargs["speaker_id"] == 42
