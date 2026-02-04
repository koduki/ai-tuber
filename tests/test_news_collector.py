import pytest
from unittest.mock import MagicMock, patch
from scripts.news_collector.tools import search_web

def test_search_web_success():
    """
    search_webが正常に結果をフォーマットして返すかテスト
    """
    mock_results = [
        {'title': 'Test Title 1', 'href': 'http://example.com/1', 'body': 'Test Snippet 1'},
        {'title': 'Test Title 2', 'href': 'http://example.com/2', 'body': 'Test Snippet 2'}
    ]

    with patch('scripts.news_collector.tools.DDGS') as MockDDGS:
        mock_instance = MockDDGS.return_value
        mock_instance.text.return_value = mock_results

        result = search_web("test query")

        assert "Test Title 1" in result
        assert "http://example.com/1" in result
        assert "Test Snippet 1" in result
        assert "Test Title 2" in result

def test_search_web_no_results():
    """
    結果が空の場合の挙動をテスト
    """
    with patch('scripts.news_collector.tools.DDGS') as MockDDGS:
        mock_instance = MockDDGS.return_value
        mock_instance.text.return_value = []

        result = search_web("unknown query")
        assert "結果が見つかりませんでした" in result

def test_search_web_exception():
    """
    例外発生時のハンドリングをテスト
    """
    with patch('scripts.news_collector.tools.DDGS') as MockDDGS:
        mock_instance = MockDDGS.return_value
        mock_instance.text.side_effect = Exception("API Error")

        result = search_web("error query")
        assert "ウェブ検索エラー: API Error" in result
