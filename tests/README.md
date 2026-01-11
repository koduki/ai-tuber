# AI Tuber テストガイド

このプロジェクトのテストスイートは、カバレッジと信頼性を最大化するために3つのカテゴリ（Unit, Integration, E2E）に分かれています。

## テストの定義

| カテゴリ | LLM | 内部インフラ | 説明 |
| :--- | :--- | :--- | :--- |
| **Unit** | モック | 利用しない | 関数やクラス単体を完全に独立させて検証します。 |
| **Integration** | **実機 (Real)** | モック (In-process) | LLMとの連携やエージェントの推論ロジック、ツールの組み合わせをPythonプロセス内で検証します。 |
| **E2E** | **実機 (Real)** | **実稼働 (SSE/HTTP)** | Dockerコンテナ等を起動し、システム全体の通信を含めて検証します。 |

---

## テストの実行方法

### 1. ユニットテスト (`tests/unit/`)
```bash
pytest tests/unit/
```

### 2. インテグレーションテスト (`tests/integration/`)
モックされたツールやサーバーを使い、内部ロジックを検証します。

```bash
# MCPサーバー単体の検証
pytest tests/integration/test_mcp_body_cli.py

# エージェントのシナリオ検証（実LLM使用）
GOOGLE_API_KEY=your_key pytest tests/integration/test_agent_scenarios.py
```

### 3. E2Eテスト (`tests/e2e/`)
Dockerコンテナを起動し、システム全体の結合を確認します。

```bash
pytest tests/e2e/
```

### 全テストの実行
```bash
pytest
```

---

## ADK Telemetry (デバッグ)

エージェントの推論プロセスやツール呼び出しの詳細を確認するために、ADK Telemetryを有効にできます。`ConsoleSpanExporter` を使用して標準出力にトレース情報を出力します。

### 有効化の方法
環境変数 `ADK_TELEMETRY=true` を設定して実行します。

```bash
# 統合テストで有効化
ADK_TELEMETRY=true GOOGLE_API_KEY=your_key pytest tests/integration/test_agent_scenarios.py
```

### 活用シーン
- LLMがなぜ特定のツールを呼んだのか（あるいは呼ばなかったのか）を確認したい時
- ツール実行の順序や引数の詳細をデバッグしたい時
- エージェントの内部フローを可視化したい時
