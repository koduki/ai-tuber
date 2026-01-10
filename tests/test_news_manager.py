import os
import json
import pytest
from src.saint_graph.news_manager import NewsManager

@pytest.fixture
def news_file(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    f = d / "news.json"
    content = {
        "date": "2023-01-01",
        "segments": [
            {"category": "test1", "content": "content1"},
            {"category": "test2", "content": "content2"}
        ]
    }
    f.write_text(json.dumps(content), encoding="utf-8")
    return str(f)

def test_load_news(news_file):
    nm = NewsManager(news_file)
    assert len(nm.segments) == 2
    assert nm.segments[0]["category"] == "test1"

def test_iteration(news_file):
    nm = NewsManager(news_file)

    assert nm.has_next() is True

    # First segment
    seg1 = nm.get_next_segment()
    assert seg1["content"] == "content1"
    nm.mark_completed()

    # Second segment
    assert nm.has_next() is True
    seg2 = nm.get_next_segment()
    assert seg2["content"] == "content2"
    nm.mark_completed()

    # Finished
    assert nm.has_next() is False
    assert nm.get_next_segment() is None

def test_missing_file():
    nm = NewsManager("non_existent_file.json")
    assert len(nm.segments) == 0
    assert nm.has_next() is False
