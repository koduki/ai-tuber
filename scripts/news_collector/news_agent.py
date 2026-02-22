import sys
import os
import argparse
import datetime
import logging
import asyncio
import re

# プロジェクトルートとsrcをsys.pathに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(project_root, "src")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

# 検索ツールのインポート
from google.adk.tools.google_search_tool import GoogleSearchTool

# インフラ（StorageClient）のインポート
from infra.storage_client import create_storage_client

# 設定
try:
    from saint_graph.config import MODEL_NAME
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
    tools = [GoogleSearchTool(bypass_multi_tools_limit=True)]

    # システム指示をファイルから読み込む
    prompt_path = os.path.join(current_dir, "system_prompt.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
    except Exception as e:
        logger.error(f"システムプロンプトの読み込みに失敗しました: {e}")
        # フォールバック（最低限の指示）
        system_instruction = "あなたはプロのニュース編集者です。Markdown形式でニュース原稿を作成してください。"

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

    # ユーザープロンプトをファイルから読み込んでフォーマット
    user_prompt_path = os.path.join(current_dir, "user_prompt.md")
    try:
        with open(user_prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        prompt_text = prompt_template.format(target_date=target_date, themes=', '.join(themes))
    except Exception as e:
        logger.error(f"ユーザープロンプトの読み込みまたはフォーマットに失敗しました: {e}")
        prompt_text = f"対象日: {target_date}, テーマ: {', '.join(themes)} に関するニュースをレポートしてください。"

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

    cleaned_response = clean_news_script(full_response)
    
    # ストレージクライアントの初期化
    storage = create_storage_client()
    
    # 論理パスの決定 (data/ 配下を StorageClient が管理)
    logical_key = "news/news_script.md"
    
    # ローカルおよびリモートに保存
    try:
        # ローカル側の出力をトリガーにするのではなく、StorageClient 経由で保存を抽象化
        # まずは一時的に書き出したファイルをアップロード（将来的に write_text も追加可能）
        local_output_path = os.path.join(project_root, "data", logical_key)
        os.makedirs(os.path.dirname(local_output_path), exist_ok=True)
        
        with open(local_output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_response)
        
        logger.info(f"ニュース原稿を保存しました: {local_output_path}")

        # GCS (または設定されたストレージ) にアップロード
        # STORAGE_TYPE=gcs の場合のみアップロードを実行
        if os.getenv("STORAGE_TYPE") == "gcs":
            storage.upload_file(key=logical_key, src=local_output_path)
            logger.info(f"ストレージにアップロードしました: {logical_key}")
            print(f"アップロード完了: {logical_key}")
        
    except Exception as e:
        logger.error(f"保存/アップロードエラー: {e}")
        print(f"警告: 保存に失敗しました: {e}")

def remove_apologetic_phrases(text: str) -> str:
    """
    「見つかりませんでした」系の言い訳フレーズを削除する。
    """
    ignore_patterns = [
        r"^.*見つかりませんでした。?.*$",
        r"^.*は見つかりませんでしたが、?.*$",
        r"^.*に関するデータはありません。?.*$",
        r"^.*具体的な.*は見つかりませんでした。?.*$",
    ]
    lines = text.split("\n")
    processed_lines = []
    for line in lines:
        is_ignored = False
        for pattern in ignore_patterns:
            if re.search(pattern, line):
                if "。しかし、" in line or "が、" in line:
                    parts = re.split(r"。しかし、|が、", line, maxsplit=1)
                    if len(parts) > 1:
                        line = parts[1].strip()
                        if not line:
                            is_ignored = True
                    else:
                        is_ignored = True
                else:
                    is_ignored = True
                break
        if not is_ignored and line.strip():
            processed_lines.append(line)
            
    return "\n".join(processed_lines).strip()

def clean_news_script(text: str) -> str:
    """
    ニュース原稿のポストプロセス：
    - Markdownコードブロックの除去
    - 重複出力の防止
    - 「見つかりませんでした」等の言い訳フレーズの除去
    """
    cleaned = text.strip()
    
    # markdownコードブロックがある場合は削除
    if cleaned.startswith("```markdown"):
        cleaned = cleaned[11:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    # 重複出力対策：最初の "# News Script" から開始し、もし2つ目があればそれ以降を削除
    if "# News Script" in cleaned:
        parts = cleaned.split("# News Script")
        if len(parts) > 2:
            cleaned = "# News Script" + parts[1]
        else:
            cleaned = "# News Script" + "".join(parts[1:])
    
    cleaned = cleaned.strip()

    cleaned = cleaned.strip()

    # 「見つかりませんでした」系のフレーズをプログラムレベルで削除
    result = remove_apologetic_phrases(cleaned)
    return result

def main():
    parser = argparse.ArgumentParser(description="ニュース収集エージェント")
    default_themes = "気になるアニメやVTuberの話題|全国の天気予報|本日の経済指標(S&P500, 日経平均, 為替ドル円, ビットコイン, 金)|経済関連ニュース|国内の政治経済ニュース|最新テックニュース"
    parser.add_argument("--themes", type=str, default=default_themes, help="パイプ(|)区切りのテーマ")
    parser.add_argument("--date", type=str, default=None, help="対象日 (YYYY-MM-DD)。デフォルトは今日。")

    args = parser.parse_args()

    target_date = args.date
    if not target_date:
        target_date = datetime.date.today().strftime("%Y-%m-%d")

    themes = [t.strip() for t in args.themes.split("|")]

    asyncio.run(run_agent(themes, target_date))

if __name__ == "__main__":
    main()
