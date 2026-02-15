"""
ニュースキャスターフローの統合テスト。

broadcast_loop のハンドラを使って、ニュース読み上げ → コメント割り込み → 
ニュース続行 のフローを検証します。
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from saint_graph.news_service import NewsService, NewsItem
from saint_graph.broadcast_loop import (
    BroadcastPhase,
    BroadcastContext,
    handle_news,
)


@pytest.fixture
def news_file_path():
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp:
        tmp.write("# News\n\n## Weather\nSunny\n\n## Economy\nStocks Up")
        tmp_path = tmp.name
    
    yield tmp_path
    
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


def _make_ctx(news_service, comments=None):
    mock_saint = MagicMock()
    mock_saint.process_turn = AsyncMock()
    mock_saint.body = MagicMock()
    mock_saint.body.get_comments = AsyncMock(return_value=comments or [])

    templates = {
        "intro": "Intro",
        "news_reading": "News: {title}\n{content}",
        "news_finished": "All news read",
        "closing": "Goodbye",
    }

    return BroadcastContext(
        saint_graph=mock_saint,
        news_service=news_service,
        templates=templates,
    )


@pytest.mark.asyncio
async def test_news_reading_flow(news_file_path):
    """ニュース読み上げ → コメント割り込み → ニュース続行 のフロー。"""
    news_service = NewsService(news_file_path)
    news_service.load_news()

    # --- Iteration 1: コメントなし → ニュース1本目を読む ---
    ctx = _make_ctx(news_service)

    phase = await handle_news(ctx)

    assert phase == BroadcastPhase.NEWS
    ctx.saint_graph.process_turn.assert_called_once()
    call_args = ctx.saint_graph.process_turn.call_args
    assert "Weather" in call_args.args[0]

    # --- Iteration 2: コメント到着 → コメント応答（ニュースは進まない） ---
    ctx.saint_graph.body.get_comments.return_value = [
        {"author": "User", "message": "Hello newscaster!"}
    ]
    ctx.saint_graph.process_turn.reset_mock()

    phase = await handle_news(ctx)

    assert phase == BroadcastPhase.NEWS
    ctx.saint_graph.process_turn.assert_called_once()
    assert "User: Hello newscaster!" in ctx.saint_graph.process_turn.call_args.args[0]
    # ニュースは進んでいない (Economy はまだ未読)
    assert news_service.has_next() is True

    # --- Iteration 3: コメントなし → ニュース2本目を読む ---
    ctx.saint_graph.body.get_comments.return_value = []
    ctx.saint_graph.process_turn.reset_mock()

    phase = await handle_news(ctx)

    assert phase == BroadcastPhase.NEWS
    call_args = ctx.saint_graph.process_turn.call_args
    assert "Economy" in call_args.args[0]

    # --- Iteration 4: ニュース全消化 → IDLE へ ---
    ctx.saint_graph.process_turn.reset_mock()

    phase = await handle_news(ctx)

    assert phase == BroadcastPhase.IDLE
    assert news_service.has_next() is False
