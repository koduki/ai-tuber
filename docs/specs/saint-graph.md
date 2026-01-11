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
    *   `runner.run_async(...)` を呼び出して非同期にイベントを処理します。
    *   **Logical Control (Nudge Logic):** LLMが自律的にツール（特に `speak`）を呼び出さない場合や、情報を検索せずに勝手に予想して回答しようとする場合に、システム側から自動的に「催促（Nudge）」メッセージを送信する制御ロジックを実装しています。
        *   **Retry Mechanism:** 最大3回まで、不足しているアクション（情報検索、発話など）を特定して再試行を促します。
        *   **Context Management:** 同一ターン内での履歴管理を行い、LLMが自身の過去の振る舞いを踏まえて修正できるように制御します。
    *   **Robust Event Detection:** 
        *   `is_tool_call` ヘルパーにより、イベントオブジェクトの文字列表現からツール呼び出し（`speak`, `get_weather` 等）と通常のテキスト出力を正確に区別します。
        *   予期せぬ生テキスト出力（Forbidden Raw Text）を検知し、ツール使用を強制します。

*   **Logic: Direct Tool Call (`call_tool`)**
    *   ポーリング（コメント取得など）のために、LLMの推論を介さずツールを直接実行するユーティリティ。
    *   **Tool Discovery & Caching:** 接続されているすべてのツールをキャッシュし、2回目以降の検索を高速化します。
    *   **Connection Resilience:** SSE接続のウォームアップ時間を考慮し、ツールが見つからない場合に最大5回（5秒間）の再試行を行います。
    *   **Result Handling:** MCPツールの実行結果（`CallToolResult`オブジェクトまたは辞書）から、テキストコンテンツを堅牢に抽出して文字列として返します。

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
*   **Agent Framework:** Google ADK (Agent Development Kit) v1.22.0+
*   **LLM:** Google Gemini
*   **Concurrency:** `asyncio` base

## Technical Implementation Notes
*   **ADK Signature Requirement:** `Runner.run_async` は位置引数を1つ (`self`) のみ受け取り、その他 (`new_message`, `user_id`, `session_id`) は**すべてキーワード専用引数**として渡す必要があります。これを怠ると `TypeError` が発生します。
*   **Context Management:** `run_async` を複数回呼び出す場合、セッション状態を維持するために `user_id` と `session_id` を固定して使用します。
*   **Telemetry:** `ADK_TELEMETRY=true` の場合、OpenTelemetry (`ConsoleSpanExporter`) により詳細な実行トレースがコンソールに出力されます。これには Nudge ロジックの発動状況なども含まれます。
*   **Robustness:** ポーリング（`call_tool`）においては、接続確立までの遅延を許容するためのリトライ機構が必須です。
