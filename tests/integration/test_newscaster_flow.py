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
    mock_saint = MagicMock(spec=SaintGraph)
    mock_saint.process_turn = AsyncMock()
    mock_saint.body = MagicMock()
    mock_saint.body.get_comments = AsyncMock(return_value=[])

    # 3. Simulate Main Loop Logic
    # Iteration 1: No comments -> Speak News Item 1
    comments_data = await mock_saint.body.get_comments()
    if not comments_data and news_service.has_next():
        item = news_service.get_next_item()
        await mock_saint.process_turn(user_input=f"news_context: {item.content}", context=f"Reading news: {item.title}")
    
    assert item.title == "Weather"
    mock_saint.process_turn.assert_called() 
    args, kwargs = mock_saint.process_turn.call_args
    assert "Reading news: Weather" in kwargs['context']

    # Iteration 2: Comment arrives -> Interrupt/Commentary
    mock_saint.body.get_comments.return_value = [{"author": "User", "message": "Hello newscaster!"}]
    comments_data = await mock_saint.body.get_comments()
    if comments_data:
        comments_text = "\n".join([f"{c.get('author', 'User')}: {c.get('message', '')}" for c in comments_data])
        await mock_saint.process_turn(user_input=comments_text)
    
    mock_saint.process_turn.assert_called_with(user_input="User: Hello newscaster!")

    # Iteration 3: No comments -> Speak News Item 2
    mock_saint.body.get_comments.return_value = []
    comments_data = await mock_saint.body.get_comments()
    if not comments_data and news_service.has_next():
        item = news_service.get_next_item()
        await mock_saint.process_turn(user_input=f"news_context: {item.content}", context=f"Reading news: {item.title}")

    assert item.title == "Economy"
    assert news_service.has_next() is False
