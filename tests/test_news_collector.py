import pytest
import sys
import os

# プロジェクトルートをsys.pathに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.news_collector.news_agent import clean_news_script

def test_clean_news_script_basic():
    """
    基本的なクリーンアップ（Markdownコードブロックの除去）をテスト
    """
    text = "```markdown\n# News Script\n## Topic\nContent\n```"
    result = clean_news_script(text)
    assert result == "# News Script\n## Topic\nContent"

def test_clean_news_script_deduplication():
    """
    重複出力の防止をテスト
    """
    text = "# News Script\nContent 1\n# News Script\nContent 2"
    result = clean_news_script(text)
    assert result == "# News Script\nContent 1"

def test_clean_news_script_ignore_phrases():
    """
    「見つかりませんでした」系のフレーズ除去をテスト
    """
    text = "# News Script\n## Topic\nデータは見つかりませんでした。\n具体的な情報は見つかりませんでした。\n有効なニュースです。"
    result = clean_news_script(text)
    assert "Topic" in result
    assert "見つかりませんでした" not in result
    assert "有効なニュースです。" in result

def test_clean_news_script_but_handling():
    """
    「...が、...」などの接続詞を伴う場合の除去をテスト
    """
    text = "# News Script\n## Topic\n具体的なデータは見つかりませんでしたが、一般的な傾向をお伝えします。\nしかし、最新の状況は良好です。"
    result = clean_news_script(text)
    assert "一般的な傾向をお伝えします。" in result
    assert "最新の状況は良好です。" in result
    assert "具体的なデータは見つかりませんでした" not in result
