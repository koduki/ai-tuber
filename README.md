# AI Tuber (Hybrid REST/MCP Architecture)

Google Agent Development Kit (ADK) と Model Context Protocol (MCP) に加え、確実な身体操作のための REST API を組み合わせた、次世代 AITuber 構築プロジェクトです。

## 特徴

*   **ハイブリッド構成**: 
    *   **REST API**: 発話、表情、録画制御など、絶対に失敗したくない「身体操作」に使用。
    *   **MCP**: 天気予報や知識検索など、AI が自律的に判断して使う「外部ツール」に使用。
*   **感情パース**: AI の生成テキストから `[emotion: happy]` のようなタグを自動でパースし、リアルタイムにアバターの表情を切り替えます。
*   **モジュール化**: 魂 (Logic)、精神 (Persona/Character)、身体 (IO/Control) が完全に分離されており、新しいキャラクターの追加が容易です。

## アーキテクチャ

*   **Saint Graph (魂)**: Google ADK をベースにした意思決定エンジン。
*   **Mind (精神)**: `data/mind/` 以下に配置される、ペルソナ、プロンプト、アセットのパッケージ。
*   **Body (肉体)**: OBS 制御、音声合成、YouTube 連携を担う REST API サービス。

### システム構成

| サービス | 役割 | ポート | 通信方式 |
|---------|------|--------|---------|
| `saint-graph` | 思考・対話エンジン | - | REST Client / MCP Client |
| `body-streamer` | ストリーミング制御ハブ | 8002 | REST API |
| `body-cli` | 開発用 CLI 入出力 | 8000 | REST API |
| `tools-weather` | 天気情報取得ツール | 8001 | MCP (SSE) |
| `obs-studio` | 配信・映像合成 | 8080, 4455 | VNC / WebSocket |
| `voicevox` | 音声合成エンジン | 50021 | HTTP API |

詳細は [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) を参照してください。

## Quick Start

### 1. 設定

`.env` ファイルを作成し、Gemini API キーを設定してください:

```bash
GOOGLE_API_KEY="your_api_key_here"
OBS_PASSWORD="" # オプション
```

### 2. 実行

全サービス（本番ストリーミング構成）を起動します:

```bash
docker compose up --build
```

### 3. OBS 設定 (初回のみ)

1. ブラウザで `http://localhost:8080/vnc.html` にアクセス。
2. OBS で「Missing Files」警告が出た場合、「Search Directory...」をクリック。
3. `/app/assets/` ディレクトリを選択して適用。

## 開発とテスト

### 開発用 CLI モード

`docker attach` を使用して、AI と直接テキストで対話できます。

```bash
docker attach app-body-cli-1
```
> **入力例**: `こんにちは`  
> **出力例**: `[AI (joyful)]: 面を上げよ！わらわこそが紅月れんじゃ！`

### テストの実行

```bash
# 全テスト実行
pytest

# ユニットテストのみ
pytest tests/unit/

# インテグレーションテストのみ
pytest tests/integration/
```

## キャラクターの追加

`data/mind/{character_name}/` ディレクトリを作成し、必要な Markdown ファイルと画像を配置するだけで、新しいキャラクターを構築できます。
詳細は [キャラクターパッケージ仕様書](docs/specs/character-package-specification.md) を参照してください。

## ドキュメント

*   [詳細アーキテクチャ](docs/ARCHITECTURE.md)
*   [Saint Graph 仕様](docs/specs/saint-graph.md)
*   [Body Streamer 仕様](docs/specs/body-streamer-architecture.md)
*   [キャラクター定義ガイド](docs/specs/character-package-specification.md)