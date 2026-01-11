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

## テストの設計方針

### モック化の基準
- **外部API**: 完全にモック化（天気API等。テストデータの安定化のため）。
- **インフラ**: IntegrationテストではSSEやHTTPサーバーをモック化し、E2Eテストでは実稼働させます。
- **LLM**: Integrationテスト（シナリオ）およびE2Eテストでは実際のGemini APIを使用します。

### 検証の優先度
1. **最優先**: ツール呼び出しのシーケンス（例: `get_weather` → `speak` の順序）。
2. **次優先**: ツールへの引数が適切であること。
3. **対象外**: LLMの出力する具体的な日本語文言（「晴れです」か「快晴じゃぞ」かは問わない）。

**重要な設計判断:**
- **本番ペルソナの使用**: テスト専用の指示は極力避け、本番の `persona.md` の指示が十分であるかを検証します。
- **スキップ設定**: LLMを使用するテストはAPIキーがない環境やGitHub Actionsでは自動的にスキップされます。
