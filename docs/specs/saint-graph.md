# SaintGraph Architecture Specification

## 概要
SaintGraphは、AI Tuberの「脳」となる中核モジュールです。
「Mind（人格）」と「Body（肉体/外部ツール）」を統合し、Google Geminiモデルを用いて対話ループを実行します。
`src/saint_graph/saint_graph.py` に実装されています。

## Core Components

### 1. SaintGraph (`saint_graph.py`)
対話制御を行うメインクラス。

*   **Responsibilities:**
    *   **Context Management:** 会話履歴の管理、Geminiの制約（role順序等）に合わせた履歴の正規化。
    *   **Inner Loop:** ユーザー入力から始まり、モデル生成、ツール実行、再生成を繰り返す自律ループ。
    *   **Streaming:** 応答のリアルタイム性を高めるためのストリーミング生成と蓄積。

*   **Logic: Turn Processing (`process_turn`)**
    1.  **User Input:** ユーザー入力を `user` roleで履歴に追加。
    2.  **Request Prep:** ベースリクエスト (`SystemInstruction` + `Tools`) に現在の `chat_history` を注入。
    3.  **Generation Loop:**
        *   `_generate_and_accumulate` を呼び出し、ストリーミングで回答を生成。
        *   **Empty Check:** 応答が空の場合、履歴整合性を保つため空文字を追加してループ終了。
        *   **Function Call Check:** 生成結果に `function_call` が含まれるか確認。
        *   **Tool Execution:**
            *   Yes: `_execute_tools` でツールを実行 -> 結果をHistoryに追加 -> **Loop継続** (Re-generate)。
            *   No: 通常のテキスト応答とみなし、Loop終了。

*   **Logic: History Management (`add_history`)**
    *   **Role Merging:** 連続するメッセージが同じ Role の場合、新しいメッセージの `parts` を既存メッセージにマージします（Gemini APIの制約回避）。
    *   **Windowing:** `HISTORY_LIMIT` を超えた場合、古いメッセージから削除します。
    *   **Start Adjustment:** 履歴の先頭が `model` role になっている場合、それを削除して必ず `user` role から始まるように調整します。

*   **Logic: Streaming Strategy (`_generate_and_accumulate`)**
    *   `model.generate_content_async(stream=True)` を使用。
    *   **Logging:** `partial=True` チャンクはログ出力（インクリメンタル表示）のみに使用し、履歴には追加しません。
    *   **Final Content:** `partial=False` の最終チャンクのみを正規の応答として採用し、重複実行（Function Callの二重発火など）を防止します。


### 2. Mind (`src/mind/`)
キャラクターの人格定義。
*   ファイルベース (`persona.md`) で管理。
*   `load_persona(name)` により動的に読み込み、LLMの `SystemInstruction` として注入される。

### 3. Application Flow (`main.py`)
1.  **Initialize:** MCP Server (Body) へ接続。
2.  **Load Mind:** 指定されたPersonaを読み込み。
3.  **Discover Tools:** MCPからツール定義を取得し、Gemini Tool形式へ変換。
4.  **Chat Loop:**
    *   `get_comments` ツールをポーリング。
    *   新規コメントがあれば `SaintGraph.process_turn` を起動。

## Technical Stack
*   **Language:** Python 3.11+
*   **LLM:** Google Gemini (via `google-genai-sdk`)
*   **Concurrency:** `asyncio` base
