# AI Tuber (Architecture Refactored)

Model Context Protocol (MCP) と Google Agent Development Kit (ADK) を活用した AI Agent 構築の実験プロジェクトです。

## アーキテクチャ

各コンポーネントを以下の様にモジュール化することで柔軟性な構成を確保します。

*   **Saint Graph (魂)**: AIエージェントとしてのコアロジック
*   **Mind (精神)**: ペルソナ設定やシステム指示などキャラクター性
*   **Body (肉体)**: CLIやYouTube、OBSといったツールや入出力機能

## Quick Start

### 設定

`.env` ファイルまたは環境変数で API キーを設定してください:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 実行方法 (開発)

このプロジェクトには `devcontainer` 設定が含まれています。VS Code でフォルダを開き、「コンテナーで再度開く」を選択してください。

**DevContainer の構成:**
- 専用の `dev` サービスが開発環境として起動します
- `body-cli` サービスは自動的にバックグラウンドで起動します
- `body-weather` サービスは自動的にバックグラウンドで起動します
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

CLIからの入力は以下のようにコンテナにattachして実行

```bash
vscode ➜ /app $ docker attach app-body-cli-1
こんにちは
[Expression]: happy
[AI (happy)]: こんにちはなのじゃ！
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

## デバッグ (ADK Telemetry)

エージェントの内部動作（思考、ツール呼び出し）を詳細に確認したい場合、ADK Telemetryを有効化できます。

```bash
ADK_TELEMETRY=true PYTHONPATH=src python -m saint_graph.main
```

詳細は [tests/README.md](tests/README.md) を参照してください。