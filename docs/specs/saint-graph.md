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
            *   Yes: `_execute_tools` でツールを実行。
            *   **ID Propagation:** ツール実行結果のレスポンスには、LLMが生成した `FunctionCall` の `id` を必ず含めます（`400 INVALID_ARGUMENT` エラーの防止）。
            *   結果をHistoryに追加 -> **Loop継続** (Re-generate)。
            *   No: 通常のテキスト応答とみなし、Loop終了。

*   **Logic: History Management (`add_history`)**
    *   **Role Merging:** 連続するメッセージが同じ Role の場合、新しいメッセージの `parts` を既存メッセージにマージします（Gemini APIの制約回避）。
    *   **Windowing:** `HISTORY_LIMIT` を超えた場合、古いメッセージから削除します。
    *   **Start Adjustment:** 履歴の先頭が `model` role になっている場合、それを削除して必ず `user` role から始まるように調整します。

*   **Logic: Streaming Strategy (`_generate_and_accumulate`)**
    *   `model.generate_content_async(stream=True)` を使用。
    *   **Parts Accumulation:** チャンクごとに取得される `parts` をすべて収集し、最終的な `Content` オブジェクトを構築します。
    *   **Tool Deduplication:** 1回のターンで同じツールの呼び出しが重複しないよう、ツール名ベースで最初の呼び出しのみを有効化します。
    *   **Final Content:** 全チャンクの読み込み完了後、蓄積された `parts` を履歴に追加します。


### 2. Mind (`src/mind/`)
キャラクターの人格定義。
*   ファイルベース (`persona.md`) で管理。
*   `load_persona(name)` により動的に読み込まれ、`src/saint_graph/core_instructions.md`（共通ルール）と結合して、LLMの `SystemInstruction` として注入される。
*   **Structure:**
    *   `core_instructions.md`: 技術的制約、ツール使用ルール、感情パラメータ定義（Emotional Parameters）。
    *   `persona.md`: キャラクター固有のアイデンティティ（Core Identity）、口調、Few-Shot。

### 3. Application Flow (`main.py`)
1.  **Initialize:** MCP Server (Body) への接続。`MCP_URLS` リストを使い、複数のサーバ（CLI, Weather 等）に同時接続します。
2.  **Load Mind:** 指定されたPersonaを読み込み。
3.  **Discover Tools:** 接続された**すべてのMCPサーバ**からツール定義を収集し、Gemini Tool形式へ変換。
4.  **Chat Loop:**
    *   `get_comments` ツールをポーリング。
    *   新規コメントがあれば `SaintGraph.process_turn` を起動。

## Technical Stack
*   **Language:** Python 3.11+
*   **LLM:** Google Gemini (via `google-genai-sdk`)
*   **Concurrency:** `asyncio` base
