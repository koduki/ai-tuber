from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)

def search_web(query: str) -> str:
    """
    DuckDuckGoを使用してウェブを検索します。
    上位10件の結果をフォーマットされた文字列として返します。
    """
    try:
        # max_results はデフォルトで10ですが、明示的に指定します。
        results = DDGS().text(keywords=query, max_results=10)

        if not results:
            return "結果が見つかりませんでした。"

        formatted_results = []
        for r in results:
            title = r.get('title', 'タイトルなし')
            link = r.get('href', 'リンクなし')
            snippet = r.get('body', 'スニペットなし')
            formatted_results.append(f"タイトル: {title}\nリンク: {link}\nスニペット: {snippet}\n")

        return "\n---\n".join(formatted_results)
    except Exception as e:
        logger.error(f"検索に失敗しました: {e}")
        return f"ウェブ検索エラー: {str(e)}"
