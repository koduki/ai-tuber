"""
broadcast_loop.py のフェーズハンドラのユニットテスト。
SaintGraph の高レベルメソッド (process_intro 等) を呼び出すことを検証します。
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from saint_graph.broadcast_loop import (
    BroadcastPhase,
    BroadcastContext,
    handle_intro,
    handle_news,
    handle_idle,
    handle_closing,
)
from saint_graph.config import MAX_WAIT_CYCLES

def _make_ctx(news_service=None, comments=None):
    mock_saint = MagicMock()
    # 新しいメソッドの AsyncMock 化
    mock_saint.process_turn = AsyncMock()
    mock_saint.process_intro = AsyncMock()
    mock_saint.process_news_reading = AsyncMock()
    mock_saint.process_news_finished = AsyncMock()
    mock_saint.process_closing = AsyncMock()
    
    mock_saint.body = MagicMock()
    mock_saint.body.get_comments = AsyncMock(return_value=comments or [])
    mock_saint.body.wait_for_queue = AsyncMock()

    mock_news = news_service or MagicMock()

    return BroadcastContext(
        saint_graph=mock_saint,
        news_service=mock_news,
    )


@pytest.mark.asyncio
async def test_handle_intro():
    ctx = _make_ctx()
    phase = await handle_intro(ctx)
    
    assert phase == BroadcastPhase.NEWS
    ctx.saint_graph.process_intro.assert_called_once()


@pytest.mark.asyncio
async def test_handle_news_with_comment():
    ctx = _make_ctx(comments=[{"author": "User", "message": "Hi"}])
    phase = await handle_news(ctx)
    
    assert phase == BroadcastPhase.NEWS
    # コメント応答は process_turn を直接呼ぶ（共通ユーティリティ）
    ctx.saint_graph.process_turn.assert_called_once()
    assert "User: Hi" in ctx.saint_graph.process_turn.call_args[0][0]
    ctx.saint_graph.process_news_reading.assert_not_called()


@pytest.mark.asyncio
async def test_handle_news_reading():
    news_service = MagicMock()
    news_service.has_next.side_effect = [True, False]
    item = MagicMock()
    item.title = "Title"
    item.content = "Content"
    news_service.peek_current_item.return_value = item
    news_service.get_next_item.return_value = item
    
    ctx = _make_ctx(news_service=news_service)
    phase = await handle_news(ctx)
    
    assert phase == BroadcastPhase.NEWS
    ctx.saint_graph.process_news_reading.assert_called_once_with(
        title="Title", content="Content"
    )


@pytest.mark.asyncio
async def test_handle_news_finished():
    news_service = MagicMock()
    news_service.has_next.return_value = False
    
    ctx = _make_ctx(news_service=news_service)
    phase = await handle_news(ctx)
    
    assert phase == BroadcastPhase.IDLE
    ctx.saint_graph.process_news_finished.assert_called_once()


@pytest.mark.asyncio
async def test_handle_idle_wait():
    ctx = _make_ctx()
    phase = await handle_idle(ctx)
    
    assert phase == BroadcastPhase.IDLE
    assert ctx.idle_counter == 1


@pytest.mark.asyncio
async def test_handle_idle_timeout():
    ctx = _make_ctx()
    ctx.idle_counter = MAX_WAIT_CYCLES  # Set to max so next increment triggers timeout
    phase = await handle_idle(ctx)
    
    assert phase == BroadcastPhase.CLOSING


@pytest.mark.asyncio
async def test_handle_closing():
    ctx = _make_ctx()
    # asyncio.sleep をモックしてテストを高速化
    with patch("asyncio.sleep", return_value=None):
        phase = await handle_closing(ctx)
    
    assert phase is None
    ctx.saint_graph.process_closing.assert_called_once()
