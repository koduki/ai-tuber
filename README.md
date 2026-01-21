# AI Tuber (Architecture Refactored)

Model Context Protocol (MCP) と Google Agent Development Kit (ADK) を活用した AI Agent 構築の実験プロジェクトです。

## アーキテクチャ

各コンポーネントを以下の様にモジュール化することで柔軟性な構成を確保します。

*   **Saint Graph (魂)**: AIエージェントとしてのコアロジック
*   **Mind (精神)**: ペルソナ設定やシステム指示などキャラクター性（プラグイン型パッケージ）
*   **Body (肉体)**: ストリーミング制御、CLI、天気など各種ツールや入出力機能

### システム構成（6サービス）

| サービス | 役割 | ポート | 備考 |
|---------|------|--------|------|
| `saint-graph` | 思考・対話エンジン | - | MCP クライアント |
| `body-desktop` | ストリーミング制御ハブ | 8002 | MCP: `/sse` |
| `body-cli` | CLI入出力（開発用） | 8000 | MCP: `/sse` |
| `body-weather` | 天気情報取得 | 8001 | MCP: `/sse` |
| `obs-studio` | 配信・映像合成 | 8080, 4455 | VNC: `/vnc.html`, WebSocket: 4455 |
| `voicevox` | 音声合成エンジン | 50021 | HTTP API |

詳細は [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) を参照してください。

## Quick Start

### 設定

`.env` ファイルまたは環境変数で API キーを設定してください:

```bash
export GOOGLE_API_KEY="your_api_key_here"

# YouTube Live連携を使用する場合（オプション）
export YOUTUBE_API_KEY="your_youtube_api_key"
export YOUTUBE_LIVE_CHAT_ID="your_live_chat_id"
```

### 実行方法

#### 本番環境（ストリーミング配信）

全サービスを起動:

```bash
docker compose up --build
```

OBS設定（初回のみ）:
1. ブラウザで `http://localhost:8080/vnc.html` にアクセス
2. OBSのMissing Filesダイアログで「Search Directory...」をクリック
3. `/app/assets/` を選択して「Apply」
4. すべてのアセットが自動的にマッピングされます

#### 開発環境（CLI）

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

**CLIからの入力:**
```bash
vscode ➜ /app $ docker attach app-body-cli-1
こんにちは
[Expression]: happy
[AI (happy)]: こんにちはなのじゃ！
```

## キャラクター管理

キャラクター定義は `data/mind/{character_name}/` にプラグイン型パッケージとして配置されます。

### 既存キャラクター

- **ren（紅月れん）**: `data/mind/ren/`

詳細は [docs/specs/character-package-specification.md](docs/specs/character-package-specification.md) を参照してください。

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

## トラブルシューティング

### OBS接続エラー

**症状**: `Failed to connect to OBS: [Errno 111] Connection refused`

**対処法**:
1. OBSコンテナが起動しているか確認: `docker compose ps`
2. OBSログを確認: `docker compose logs obs-studio`
3. 数秒待ってから再試行（OBS起動に時間がかかる場合があります）

### 音声が再生されない

**症状**: 音声ファイルは生成されるが再生されない

**対処法**:
1. VNC (`http://localhost:8080/vnc.html`) でOBSを確認
2. `audio_source` メディアソースが存在し、`/tmp/audio/` を監視していることを確認

詳細は各仕様書のトラブルシューティングセクションを参照してください。

## デバッグ (ADK Telemetry)

エージェントの内部動作（思考、ツール呼び出し）を詳細に確認したい場合、ADK Telemetryを有効化できます。

```bash
ADK_TELEMETRY=true PYTHONPATH=src python -m saint_graph.main
```

詳細は [tests/README.md](tests/README.md) を参照してください。

## ドキュメント

- [アーキテクチャ概要](docs/ARCHITECTURE.md)
- [Body Desktop仕様](docs/specs/body-desktop-architecture.md)
- [OBS Studio設定](docs/specs/obs-studio-configuration.md)
- [キャラクターパッケージ仕様](docs/specs/character-package-specification.md)