import sys
import os
import argparse
import datetime
import logging
import asyncio
import re
from google.cloud import storage

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

    # 「見つかりませんでした」系のフレーズをプログラムレベルで削除
    ignore_patterns = [
        r"^.*見つかりませんでした。?.*$",
        r"^.*は見つかりませんでしたが、?.*$",
        r"^.*に関するデータはありません。?.*$",
        r"^.*具体的な.*は見つかりませんでした。?.*$",
    ]
    lines = cleaned.split("\n")
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
    
    result = "\n".join(processed_lines)
    return result.strip()

async def run_agent(themes: list[str], target_date: str):
    logger.info(f"エージェントを初期化中: 日付={target_date}")

    # ツール定義
    tools = [GoogleSearchTool(bypass_multi_tools_limit=True)]

    # システム指示定義
    system_instruction = """
あなたはバーチャルキャラクターのためのプロのニュース編集者です。
特定のテーマと対象日に基づいてニュース原稿を編集するのがあなたの仕事です。
必ず 'google_search' ツールを使用して、最新の情報および過去の正確な情報を検索してください。

提供された各テーマについて:
1. 関連するニュース更新をウェブで検索します。クエリに対象日を含めて、最近の情報を探してください。
2. 情報をフィルタリングし、対象日に関連するものであることを確認します。
3. 要点を日本語で簡潔にまとめます。

出力形式は、'# News Script' で始まるクリーンなMarkdownファイルである必要があります。
必ず提供されたテーマの順番通りに出力してください。特に「気になるアニメやVTuberの話題」は、天気予報よりも前に配置してください。
見つかった情報の範囲内で、最も関連性の高い内容を断定的に記述してください。
以下の内容やフレーズを含めることは**厳禁**です。含まれていた場合は失敗とみなします：
- 「...は見つかりませんでした」「...は不明です」「...に関するデータはありません」
- 「検索した結果...」「...とされていますが、代わりに...」
- 「終値データは見つかりませんでしたが」などの言い訳や背景説明

もし特定の日付の正確なデータがどうしても見つからない場合は、以下のいずれかで対処してください：
1. その項目（箇条書きの1行やセクション全体）を丸ごと削除して出力しない。
2. 確信の持てる直近の傾向や関連ニュースのみを、断り書きなしで記述する。

サブカルチャー関連（アニメ・VTuber等）の話題については、以下の点に注意してください：
- ジャンプ系（週刊少年ジャンプ、少年ジャンプ＋等）の話題、およびその連載作品（例：銀魂、呪術廻戦、ONE PIECE、僕のヒーローアカデミア、チェンソーマン等）は一切含めないでください。
- 内容は非常に簡潔に、**1〜3項目厳守**（全体のボリュームの1/3以下）に抑えててください。

「国内の政治経済ニュース」については、以下の点に注意してください：
- 他のセクションよりも重点的に、少し多めのボリューム（**3〜5項目程度**）で、日本国内の話題を中心に記述してください。

事実のみをニュース原稿として自然に記述してください。
「...でしたが、代わりに...」といったつなぎ文句も避け、あたかもその情報が今日（または対象日）のニュースであるかのように構成してください。
言い訳をするくらいなら、何も書かない方がマシです。

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
「見つかりませんでした」という断り書きは不要です。検索結果から得られる最善の情報を提供してください。
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

    cleaned_response = clean_news_script(full_response)
    
    # ファイルに保存
    output_path = os.path.join(project_root, "data/news/news_script.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_response)

    logger.info(f"ニュース原稿を保存しました: {output_path}")
    print(f"更新完了。確認してください: {output_path}")
    
    # GCSへのアップロード（オプション）
    gcs_bucket = os.getenv("GCS_BUCKET_NAME")
    if gcs_bucket:
        try:
            upload_to_gcs(output_path, gcs_bucket, "news/news_script.md")
            logger.info(f"GCS バケット '{gcs_bucket}' にアップロードしました")
            print(f"GCS アップロード完了: gs://{gcs_bucket}/news/news_script.md")
        except Exception as e:
            logger.error(f"GCS アップロードエラー: {e}")
            print(f"警告: GCS アップロードに失敗しましたが、ローカルファイルは保存されています")


def upload_to_gcs(local_file_path: str, bucket_name: str, destination_blob_name: str):
    """
    ファイルをGoogle Cloud Storageにアップロードします。
    
    Args:
        local_file_path: アップロードするローカルファイルのパス
        bucket_name: GCSバケット名
        destination_blob_name: GCS内の保存先パス
    """
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    blob.upload_from_filename(local_file_path)
    logger.info(f"File {local_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}")


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
