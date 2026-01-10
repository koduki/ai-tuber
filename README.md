# AI Tuber (Architecture Refactored)

Model Context Protocol (MCP) と Google Agent Development Kit (ADK) を活用した AI Agent 構築の実験プロジェクトです。

## アーキテクチャ: "Saint Graph" & "Single Body"

システム構成を簡素化し、中心的な思考エンジン（Saint Graph）と単一の能力提供者（Body）に集約しました。

*   **Saint Graph (魂)**:
    *   **Outer Loop (`src/saint_graph/main.py`)**: アプリケーションのライフサイクルを管理し、MCP Body に接続して「ニュースループ」を実行します。
    *   **Inner Loop (`src/saint_graph/saint_graph.py`)**: LLM との対話（ターン制会話）を処理します。コンテンツ生成、ツール実行、モデルが満足するまでのループを制御します。
    *   **Mind (`src/mind`)**: ペルソナ設定やシステム指示を格納します。
    *   **MCP Client (`src/saint_graph/mcp_client.py`)**: 単一の MCP サーバーに接続する、将来の互換性を考慮したクライアントです。標準的な `list_tools` と `call_tool` メソッドを実装しています。

*   **Body (身体)**:
    *   **MCP Server (例: `src/body/cli`)**: ツールや入出力機能を提供します。Saint Graph はこの単一のエンドポイントに接続します。

## はじめに

### 必要なもの

*   Docker & Docker Compose
*   Google Gemini API Key

### 設定

`.env` ファイルまたは環境変数で API キーを設定してください:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 実行方法 (開発)

このプロジェクトには `devcontainer` 設定が含まれています。VS Code でフォルダを開き、「コンテナーで再度開く」を選択してください。

**DevContainer の構成:**
- 専用の `dev` サービスが開発環境として起動します
- `mcp-cli` サービスは自動的にバックグラウンドで起動します
- `saint-graph` は手動で起動してテストできます

**Saint Graph を手動で実行する方法:**
```bash
# DevContainer 内で実行 (/app/src を PYTHONPATH に通した状態で実行)
PYTHONPATH=src python -m saint_graph.main
```

手動でコンテナを起動する場合:

```bash
docker compose up --build
```

## テスト

このプロジェクトでは、品質を担保するために複数のレイヤーでテストを実装しています。

### テストの種類

1.  **ユニットテスト (`tests/unit`)**:
    *   `SaintGraph` の履歴管理や重複実行の防止ロジックの検証。
    *   `MCPClient` のプロトコル解析の検証。
    *   Gemini API とのやり取りにおけるエラーハンドリング。
2.  **インテグレーションテスト (`tests/integration`)**:
    *   MCP Body (FastAPI サーバー) のエンドポイントやプロトコル準拠の検証。
3.  **E2E (End-to-End) テスト (`tests/e2e`)**:
    *   `pytest-docker` を使用し、実際に Docker コンテナを起動・終了させて、システム全体の疎通とライフサイクルを検証。

### テストの実行方法

全てのテストを一括で実行するには、プロジェクトのルートディレクトリで以下のコマンドを実行します：

```bash
pytest
```

特定のレイヤーのテストのみを実行する場合：

```bash
# ユニットテストのみ
pytest tests/unit/ -v

# インテグレーションテストのみ
pytest tests/integration/ -v

# E2Eテストのみ (コンテナのビルドと起動が自動で行われます)
pytest tests/e2e/ -v -s
```

## キーコンセプト

*   **単一接続**: Saint Graph は単一の MCP エンドポイント (`MCP_URL` で定義) に接続します。
*   **標準化インターフェース**: `MCPClient` は、将来の移行を容易にするため、公式 Python SDK の `ClientSession` インターフェース (`list_tools`, `call_tool`) に合わせて設計されています。
*   **冪等性と信頼性**: ストリーミングレスポンスによる重複アクションの防止など、本番環境での信頼性を考慮した実装が含まれています。
