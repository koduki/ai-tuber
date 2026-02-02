import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from saint_graph.news_service import NewsService, NewsItem
from saint_graph.saint_graph import SaintGraph
import asyncio

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

@pytest.mark.asyncio
async def test_news_reading_flow(news_file_path):
    # 1. Setup Mock NewsService with Temp File
    news_service = NewsService(news_file_path)
    news_service.load_news()

    # 2. Setup Mock SaintGraph
    # We mock the ADK dependencies to focus on the flow control in main.py (simulated here)
    mock_saint = MagicMock(spec=SaintGraph)
    mock_saint.process_turn = AsyncMock()
    mock_saint.call_tool = AsyncMock(return_value="No new comments.")

    # 3. Simulate Main Loop Logic
    # Iteration 1: No comments -> Speak News Item 1
    comments = await mock_saint.call_tool("sys_get_comments", {})
    if comments == "No new comments." and news_service.has_next():
        item = news_service.get_next_item()
        await mock_saint.process_turn(user_input=f"news_context: {item.content}", context=f"Reading news: {item.title}")
    
    assert item.title == "Weather"
    # Note: content logic in main.py might differ slightly in string formatting
    mock_saint.process_turn.assert_called() 
    # Check if call args contain context
    args, kwargs = mock_saint.process_turn.call_args
    assert "Reading news: Weather" in kwargs['context']

    # Iteration 2: Comment arrives -> Interrupt/Commentary
    mock_saint.call_tool.return_value = "Hello newscaster!"
    comments = await mock_saint.call_tool("sys_get_comments", {})
    if comments != "No new comments.":
        await mock_saint.process_turn(user_input=comments)
    
    mock_saint.process_turn.assert_called_with(user_input="Hello newscaster!")

    # Iteration 3: No comments -> Speak News Item 2
    mock_saint.call_tool.return_value = "No new comments."
    comments = await mock_saint.call_tool("sys_get_comments", {})
    if comments == "No new comments." and news_service.has_next():
        item = news_service.get_next_item()
        await mock_saint.process_turn(user_input=f"news_context: {item.content}", context=f"Reading news: {item.title}")

    assert item.title == "Economy"
    assert news_service.has_next() is False
