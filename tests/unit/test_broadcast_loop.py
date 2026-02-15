"""
broadcast_loop のユニットテスト。

各フェーズハンドラの状態遷移と BroadcastContext の状態変化を検証します。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from saint_graph.broadcast_loop import (
    BroadcastPhase,
    BroadcastContext,
    handle_intro,
    handle_news,
    handle_idle,
    handle_closing,
    run_broadcast_loop,
    _poll_and_respond,
)
from saint_graph.news_service import NewsItem


def _make_ctx(comments=None, news_items=None):
    """テスト用の BroadcastContext を生成するヘルパー。"""
    mock_saint = MagicMock()
    mock_saint.process_turn = AsyncMock()
    mock_saint.body = MagicMock()
    mock_saint.body.get_comments = AsyncMock(return_value=comments or [])
    mock_saint.close = AsyncMock()

    mock_news = MagicMock()
    if news_items:
        _items = list(news_items)
        mock_news.has_next = MagicMock(side_effect=lambda: len(_items) > 0)
        mock_news.get_next_item = MagicMock(side_effect=lambda: _items.pop(0))
    else:
        mock_news.has_next = MagicMock(return_value=False)
        mock_news.get_next_item = MagicMock(return_value=None)

    templates = {
        "intro": "Intro template",
        "news_reading": "News: {title}\n{content}",
        "news_finished": "News finished template",
        "closing": "Closing template",
    }

    return BroadcastContext(
        saint_graph=mock_saint,
        news_service=mock_news,
        templates=templates,
    )


# ---------------------------------------------------------------------------
# handle_intro
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intro_transitions_to_news():
    ctx = _make_ctx()
    next_phase = await handle_intro(ctx)

    assert next_phase == BroadcastPhase.NEWS
    ctx.saint_graph.process_turn.assert_called_once_with("Intro template", context="Intro")


# ---------------------------------------------------------------------------
# handle_news
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_news_with_items_stays_in_news():
    items = [
        NewsItem(id="1", category="News", title="Title1", content="Body1"),
        NewsItem(id="2", category="News", title="Title2", content="Body2"),
    ]
    ctx = _make_ctx(news_items=items)

    next_phase = await handle_news(ctx)

    assert next_phase == BroadcastPhase.NEWS
    ctx.saint_graph.process_turn.assert_called_once()
    call_args = ctx.saint_graph.process_turn.call_args
    assert "Title1" in call_args.args[0]


@pytest.mark.asyncio
async def test_news_exhausted_transitions_to_idle():
    ctx = _make_ctx(news_items=[])

    next_phase = await handle_news(ctx)

    assert next_phase == BroadcastPhase.IDLE
    ctx.saint_graph.process_turn.assert_called_once_with(
        "News finished template", context="News Finished"
    )


@pytest.mark.asyncio
async def test_news_comment_takes_priority_over_news():
    """ニュースがあってもコメントがあれば、コメント応答を優先する。"""
    items = [
        NewsItem(id="1", category="News", title="Title1", content="Body1"),
    ]
    comments = [{"author": "Viewer", "message": "Hello!"}]
    ctx = _make_ctx(comments=comments, news_items=items)

    next_phase = await handle_news(ctx)

    assert next_phase == BroadcastPhase.NEWS
    # process_turn はコメント応答で呼ばれ、ニュースは読まれていない
    ctx.saint_graph.process_turn.assert_called_once()
    assert "Viewer: Hello!" in ctx.saint_graph.process_turn.call_args.args[0]
    # ニュースはまだ消化されていない
    ctx.news_service.get_next_item.assert_not_called()


# ---------------------------------------------------------------------------
# handle_idle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_idle_comment_resets_counter():
    comments = [{"author": "User", "message": "Still here!"}]
    ctx = _make_ctx(comments=comments)
    ctx.idle_counter = 10  # すでにカウントが進んでいる

    next_phase = await handle_idle(ctx)

    assert next_phase == BroadcastPhase.IDLE
    assert ctx.idle_counter == 0  # リセットされた


@pytest.mark.asyncio
async def test_idle_no_comment_increments_counter():
    ctx = _make_ctx()
    ctx.idle_counter = 5

    next_phase = await handle_idle(ctx)

    assert next_phase == BroadcastPhase.IDLE
    assert ctx.idle_counter == 6


@pytest.mark.asyncio
async def test_idle_timeout_transitions_to_closing():
    ctx = _make_ctx()
    ctx.idle_counter = 100  # MAX_WAIT_CYCLES を超えている

    with patch("saint_graph.broadcast_loop.MAX_WAIT_CYCLES", 30):
        next_phase = await handle_idle(ctx)

    assert next_phase == BroadcastPhase.CLOSING


# ---------------------------------------------------------------------------
# handle_closing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_closing_returns_none():
    ctx = _make_ctx()

    next_phase = await handle_closing(ctx)

    assert next_phase is None
    ctx.saint_graph.process_turn.assert_called_once_with(
        "Closing template", context="Closing"
    )


# ---------------------------------------------------------------------------
# _poll_and_respond
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_poll_and_respond_with_comments():
    ctx = _make_ctx(comments=[{"author": "A", "message": "Hi"}])

    result = await _poll_and_respond(ctx)

    assert result is True
    ctx.saint_graph.process_turn.assert_called_once()
    assert "A: Hi" in ctx.saint_graph.process_turn.call_args.args[0]


@pytest.mark.asyncio
async def test_poll_and_respond_no_comments():
    ctx = _make_ctx(comments=[])

    result = await _poll_and_respond(ctx)

    assert result is False
    ctx.saint_graph.process_turn.assert_not_called()


# ---------------------------------------------------------------------------
# run_broadcast_loop (統合)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_loop_runs_to_closing():
    """INTRO → NEWS (1本) → IDLE → CLOSING の全フロー。"""
    items = [
        NewsItem(id="1", category="News", title="Only", content="Single item"),
    ]
    ctx = _make_ctx(news_items=items)

    with patch("saint_graph.broadcast_loop.MAX_WAIT_CYCLES", 0), \
         patch("saint_graph.broadcast_loop.POLL_INTERVAL", 0):
        await run_broadcast_loop(ctx)

    # process_turn が少なくとも4回呼ばれる: intro, news, news_finished, closing
    assert ctx.saint_graph.process_turn.call_count >= 4
