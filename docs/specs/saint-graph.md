# SaintGraph Architecture Specification

## 概要
SaintGraphは、AI Tuberの「脳」となる中核モジュールです。
Google ADK (Agent Development Kit) を活用し、「Mind（人格）」と「Body（肉体/外部ツール）」を統合して、対話ループを効率的に実行します。
`src/saint_graph/saint_graph.py` に実装されています。

## Core Components

### 1. SaintGraph (`saint_graph.py`)
Google ADK を用いた対話制御のメインクラス。

*   **Responsibilities:**
    *   **Agent Management:** `google.adk.Agent` を使用した人格（Mind）とツール（Body）の統合。
    *   **Toolset Integration:** `McpToolset` を介した複数のMCPサーバーとの接続管理。
    *   **Turn Processing:** `InMemoryRunner` を使用した自律的な対話ループ（Inner Loop）の実行。

*   **Logic: Initialization**
    1.  **MCP Toolsets:** 設定された `MCP_URLS` に対して `SseConnectionParams` を生成し、`McpToolset` を初期化します。
    2.  **Agent:** `google.adk.Agent` を構築。モデル（Gemini）、システム指示（Mind）、およびツールセットを紐付けます。
    3.  **Runner:** `InMemoryRunner` を初期化し、セッション状態を管理します。

*   **Logic: Turn Processing (`process_turn`)**
    *   `runner.run_debug(..., verbose=False)` を呼び出します（ログ抑制のため verbose=False）。
    *   ADKの内部ループにより、以下の処理が自動化されます。
        *   ユーザー入力の履歴への追加。
        *   LLMへのリクエスト生成。
        *   ツール実行要求（function_call）のパースと実行。
        *   ツール実行結果のモデルへのフィードバックと再生成。
        *   **Important:** 情報検索系ツール（Observation）の結果を受け取った後、LLMは必ず `speak` ツールを使用して回答を行うよう、システム指示（`core_instructions.md`）で厳格に制御されます。
        *   履歴の正規化（Role順序の維持、メッセージのマージ等）。

*   **Logic: Direct Tool Call (`call_tool`)**
    *   ポーリング（コメント取得など）のために、LLMの推論を介さずツールを直接実行するユーティリティ。
    *   接続されているすべての `McpToolset` から指定された名前のツールを検索し、実行します。
    *   **Result Handling:** MCPツールの実行結果（`CallToolResult`オブジェクトまたは辞書）から、テキストコンテンツ（`content.text` または `content['result']`）を堅牢に抽出して文字列として返します。

### 2. Mind (`src/mind/`)
キャラクターの人格定義。
*   ファイルベース (`persona.md`) で管理。
*   `load_persona(name)` により動的に読み込まれ、`src/saint_graph/core_instructions.md`（共通ルール）と結合して、ADK Agentの `instruction` として注入される。

### 3. Application Flow (`main.py`)
1.  **Initialize:** `SaintGraph` インスタンスの作成。複数のMCPサーバへの接続が開始されます。
2.  **Poll Loop:**
    *   `call_tool("sys_get_comments", ...)` を定期的なインターバル（`config.POLL_INTERVAL`、デフォルト1.0秒）で呼び出し。
    *   新規コメントを検知した場合、`SaintGraph.process_turn` を起動して対話を開始。

## Technical Stack
*   **Language:** Python 3.11+
*   **Agent Framework:** Google ADK (Agent Development Kit)
*   **LLM:** Google Gemini
*   **Concurrency:** `asyncio` base
