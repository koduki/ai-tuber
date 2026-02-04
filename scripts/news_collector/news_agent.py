import sys
import os
import argparse
import datetime
import logging
import asyncio
import re

# プロジェクトルートをsys.pathに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

# 検索ツールのインポート
try:
    from scripts.news_collector.tools import search_web
except ImportError:
    # モジュール解決に失敗した場合のフォールバック
    sys.path.append(os.path.join(project_root, 'scripts'))
    from news_collector.tools import search_web

# 設定
try:
    from src.saint_graph.config import MODEL_NAME
    # GOOGLE_API_KEY は環境変数に含まれていることを想定
except ImportError:
    MODEL_NAME = "gemini-2.5-flash-lite"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("news_agent")

async def run_agent(themes: list[str], target_date: str):
    logger.info(f"エージェントを初期化中: 日付={target_date}")

    # ツール定義
    tools = [FunctionTool(search_web)]

    # システム指示定義
    system_instruction = """
あなたはバーチャルキャラクターのためのプロのニュース編集者です。
特定のテーマと対象日に基づいてニュース原稿を編集するのがあなたの仕事です。
必ず 'search_web' ツールを使用して、実際の情報を検索してください。

提供された各テーマについて:
1. 関連するニュース更新をウェブで検索します。クエリに対象日を含めて、最近の情報を探してください。
2. 情報をフィルタリングし、対象日に関連するものであることを確認します。
3. 要点を日本語で簡潔にまとめます。

出力形式は、'# News Script' で始まるクリーンなMarkdownファイルである必要があります。
以下の構造に従ってください:

# News Script

## [テーマ名]
[要約テキスト...]

## [テーマ名]
[要約テキスト...]

...

「ニュースをお伝えします」などの会話的なフィラーは含めないでください。Markdownの内容のみを出力してください。
"""

    # エージェント初期化
    agent = Agent(
        name="NewsEditor",
        model=Gemini(model=MODEL_NAME),
        instruction=system_instruction,
        tools=tools
    )

    runner = InMemoryRunner(agent=agent)

    # セッション確保
    session_id = "news_session"
    user_id = "cli_user"

    # InMemoryRunnerのapp_nameと一致させる
    app_name = runner.app_name

    session = await runner.session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    if not session:
        logger.info("Creating new session...")
        await runner.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
    else:
        logger.info("Using existing session.")

    # プロンプト
    prompt_text = f"""
対象日: {target_date}
テーマ: {', '.join(themes)}

この日付のこれらのテーマに関するニュースを見つけて、レポートを作成してください。
この日付のテーマに関する特定のニュースが見つからない場合は、検索結果に基づいて「重要なニュースは見つかりませんでした」などを記載してください。
"""

    logger.info("エージェントにプロンプトを送信中...")
    full_response = ""

    async for event in runner.run_async(
        new_message=types.Content(role="user", parts=[types.Part(text=prompt_text)]),
        user_id=user_id,
        session_id=session_id
    ):
        # イベントからテキストを抽出
        if hasattr(event, 'content') and event.content:
            parts = getattr(event.content, 'parts', [])
            for p in parts:
                if hasattr(p, 'text') and p.text:
                    full_response += p.text

    # レスポンスの整形
    cleaned_response = full_response.strip()
    # markdownコードブロックがある場合は削除
    if cleaned_response.startswith("```markdown"):
        cleaned_response = cleaned_response[11:]
    elif cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]

    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]

    cleaned_response = cleaned_response.strip()

    if not cleaned_response:
        logger.error("エージェントが空のレスポンスを返しました。")
        return

    # ファイルに保存
    output_path = os.path.join(project_root, "data/news/news_script.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_response)

    logger.info(f"ニュース原稿を保存しました: {output_path}")
    print(f"更新完了。確認してください: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="ニュース収集エージェント")
    default_themes = "全国の天気予報,本日の経済指標(S&P500, 日経平均, 為替ドル円, ビットコイン, 金),経済関連ニュース,国内の政治経済ニュース,最新テックニュース"
    parser.add_argument("--themes", type=str, default=default_themes, help="カンマ区切りのテーマ")
    parser.add_argument("--date", type=str, default=None, help="対象日 (YYYY-MM-DD)。デフォルトは今日。")

    args = parser.parse_args()

    target_date = args.date
    if not target_date:
        target_date = datetime.date.today().strftime("%Y-%m-%d")

    themes = [t.strip() for t in args.themes.split(",")]

    asyncio.run(run_agent(themes, target_date))

if __name__ == "__main__":
    main()
