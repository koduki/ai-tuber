import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
import asyncio
import os
import tempfile
from saint_graph.news_service import NewsService, NewsItem

# main.py のロジックをシミュレーションするためのテスト
# 実際の main.py は無限ループを含むため、ロジックを模倣してテストします。

@pytest.fixture
def news_file_path():
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp:
        # Markdown形式でニュースを作成
        tmp.write("# News\n\n## Title1\nThis is the full body content.\nIt has multiple lines.\n\n## Title2\nSecond news body.")
        tmp_path = tmp.name
    
    yield tmp_path
    
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

@pytest.mark.asyncio
async def test_full_news_content_reading(news_file_path):
    """
    検証項目:
    process_turn に渡される指示(instruction)に、ニュースの本文が
    「一字一句省略せずに」という指示と共に含まれているか。
    """
    # 1. Setup Mock NewsService
    news_service = NewsService(news_file_path)
    news_service.load_news()

    # 2. Setup Mock SaintGraph
    mock_saint = MagicMock()
    mock_saint.process_turn = AsyncMock()
    mock_saint.call_tool = AsyncMock(return_value="No new comments.")

    # 3. Simulate "Reading News" Logic from main.py
    if news_service.has_next():
        item = news_service.get_next_item()
        
        # main.py のロジックをコピー
        instruction = (
            f"【システム指示：ニュース読み上げ】\n"
            f"以下の「ニュース本文」を、一字一句省略せずに読み上げた上で、一連の発言として感想を述べてください。\n"
            f"導入、本文、感想を**すべて1回**の `speak` ツール呼び出しにまとめて出力してください。\n"
            f"\n"
            f"ニュースタイトル: {item.title}\n"
            f"ニュース本文:\n{item.content}\n"
        )
        
        await mock_saint.process_turn(instruction, context=f"News Reading: {item.title}")

    # 4. Assertions
    # process_turn が呼ばれたか
    assert mock_saint.process_turn.called
    args, kwargs = mock_saint.process_turn.call_args
    prompt_text = args[0]
    context = kwargs.get('context')

    # コンテキストの確認
    assert context == "News Reading: Title1"
    
    # プロンプト内容の確認
    assert "ニュース本文" in prompt_text
    assert "This is the full body content." in prompt_text
    assert "It has multiple lines." in prompt_text
    assert "**すべて1回**の `speak` ツール呼び出し" in prompt_text


@pytest.mark.asyncio
async def test_closing_interruption_logic():
    """
    検証項目:
    ニュース終了後、ユーザーコメントがあった場合に
    終了カウントダウンがリセットされるか（ロジックシミュレーション）。
    """
    # 状態変数の初期化
    finished_news = True
    end_wait_counter = 5 # すでに少しカウントが進んでいるとする
    MAX_WAIT_CYCLES = 20
    
    # Mock Objects
    mock_saint = MagicMock()
    mock_saint.process_turn = AsyncMock()
    # 1回目はコメントあり、2回目はなし
    mock_saint.call_tool = AsyncMock(side_effect=["User Comment: Don't go!", "No new comments."])

    # Loop Simulation (2 iterations)
    for _ in range(2):
        # 1. コメント確認
        has_user_interaction = False
        comments = await mock_saint.call_tool("sys_get_comments", {})
        
        if comments and comments != "No new comments.":
            await mock_saint.process_turn(comments)
            has_user_interaction = True
            # *** ここが重要なロジック ***
            end_wait_counter = 0 
        
        # 2. ニュースなし＆終了モード
        if not has_user_interaction and finished_news:
            end_wait_counter += 1
            if end_wait_counter > MAX_WAIT_CYCLES:
                await mock_saint.process_turn("Closing message...", context="Closing")
                break

    # 検証
    # 1. 最初のループでコメントがあったため、end_wait_counter は 0 にリセットされたはず
    # 2. 次のループでコメントがなかったので、end_wait_counter は 1 になったはず
    # つまり、Closing処理（MAX_WAIT_CYCLES超え）は呼ばれていないはず
    
    # process_turn は "User Comment..." で1回呼ばれたのみで、"Closing message..." は呼ばれていないこと
    calls = mock_saint.process_turn.call_args_list
    assert len(calls) == 1
    assert calls[0][0][0] == "User Comment: Don't go!"
    
    # カウンターの状態（ロジックの検証）
    assert end_wait_counter == 1
    assert end_wait_counter < MAX_WAIT_CYCLES
