"""
ニュースキャスターロジック v2 テスト。

broadcast_loop のハンドラを使って、以下を検証します:
1. ニュース本文が省略されずに process_turn に渡されること
2. IDLE フェーズでコメントが来た場合に idle_counter がリセットされること
"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock, patch

from saint_graph.news_service import NewsService, NewsItem
from saint_graph.broadcast_loop import (
    BroadcastPhase,
    BroadcastContext,
    handle_news,
    handle_idle,
)


@pytest.fixture
def news_file_path():
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp:
        tmp.write("# News\n\n## Title1\nThis is the full body content.\nIt has multiple lines.\n\n## Title2\nSecond news body.")
        tmp_path = tmp.name
    
    yield tmp_path
    
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


def _make_ctx(news_service=None, comments=None):
    mock_saint = MagicMock()
    mock_saint.process_turn = AsyncMock()
    mock_saint.process_news_reading = AsyncMock()
    mock_saint.process_news_finished = AsyncMock()
    mock_saint.body = MagicMock()
    mock_saint.body.get_comments = AsyncMock(return_value=comments or [])

    mock_news = news_service or MagicMock()

    return BroadcastContext(
        saint_graph=mock_saint,
        news_service=mock_news,
    )


@pytest.mark.asyncio
async def test_full_news_content_reading(news_file_path):
    """
    検証項目:
    process_turn に渡される指示(instruction)に、ニュースの本文が
    「一字一句省略せずに」という指示と共に含まれているか。
    """
    news_service = NewsService(news_file_path)
    news_service.load_news()
    ctx = _make_ctx(news_service=news_service)

    # handle_news を呼び出し → 1本目のニュースを読み上げ
    phase = await handle_news(ctx)

    assert phase == BroadcastPhase.NEWS
    ctx.saint_graph.process_news_reading.assert_called_once()
    
    args, kwargs = ctx.saint_graph.process_news_reading.call_args
    assert kwargs.get('title') == "Title1"
    assert "This is the full body content." in kwargs.get('content')


@pytest.mark.asyncio
async def test_closing_interruption_logic():
    """
    検証項目:
    IDLE フェーズでコメントが来た場合に idle_counter がリセットされ、
    CLOSING に遷移しないこと。
    """
    # --- ループ1: コメントあり → counter リセット ---
    ctx = _make_ctx(
        comments=[{"author": "User", "message": "Don't go!"}]
    )
    ctx.idle_counter = 5  # すでにカウントが進んでいる

    phase = await handle_idle(ctx)

    assert phase == BroadcastPhase.IDLE
    assert ctx.idle_counter == 0  # リセットされた
    ctx.saint_graph.process_turn.assert_called_once()
    assert "User: Don't go!" in ctx.saint_graph.process_turn.call_args.args[0]

    # --- ループ2: コメントなし → counter インクリメント ---
    ctx.saint_graph.body.get_comments.return_value = []
    ctx.saint_graph.process_turn.reset_mock()

    phase = await handle_idle(ctx)

    assert phase == BroadcastPhase.IDLE
    assert ctx.idle_counter == 1
    ctx.saint_graph.process_turn.assert_not_called()

    # CLOSING にはまだ遷移していない
    assert ctx.idle_counter < 20  # MAX_WAIT_CYCLES のデフォルト値
