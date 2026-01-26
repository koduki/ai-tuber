---
description: AI Newscaster アプリケーション実装仕様書
---

# アプリケーション実装仕様書: Saint Graph AI Newscaster

## 1. 概要
**Saint Graph AI Newscaster** は、LLM (Gemini) によって駆動される、キャラクター主導の自動配信システムです。Markdown ファイルからニュース原稿を読み込み、ペルソナに基づいた解説を加え、CLI を通じて視聴者と交流します。システムは Docker を使用してコンテナ化されており、Google Agent Development Kit (ADK) を活用しています。

## 2. アーキテクチャ
システムは主に 3 つの Docker サービスで構成されています。
- **`saint-graph`**: コアロジックサービス。
  - `data/news/news_script.md` からニュースをロードします。
  - AI ペルソナ（「紅月れん」）と対話フローを管理します。
  - MCP サーバー（Weather, User Comments）に接続します。
- **`body-cli`**: AI の発話を出力し、ユーザーコメントを受け付ける CLI ベースのインターフェース。
- **`tools-weather`**: MCP を通じて天気データを提供するモックサーバー。

## 3. 主要コンポーネント

### 3.1 News Service (`src/saint_graph/news_service.py`)
- **機能**: `news_script.md` を解析して `NewsItem` オブジェクトに変換します。
- **フォーマット**: `## Title` ヘッダーを持つ Markdown をサポート。
- **ロジック**:
  - `load_news()`: ファイルを読み込み、`##` で分割し、タイトルと本文を抽出します。
  - `get_next_item()`: 次の未読ニュース項目を返します。
  - `has_next()`: 未読の項目が存在するか確認します。
- **ロギング**: 標準の `logging` モジュールを使用し、デバッグ情報とエラーを適切なログレベルで記録します。

### 3.2 Main Application Loop (`src/saint_graph/main.py`)
- **初期化**:
  - `PromptLoader` を使用して、キャラクター固有のペルソナとテンプレートをロードします。
  - グローバルな指示事項 (`src/saint_graph/system_prompts/core_instructions.md`) をロードします。
  - MCP ツールと Retry Instructions を使用して `SaintGraph` を初期化します。
  - `NewsService` 経由でニュースをロードします（パスは `NEWS_DIR` 環境変数で設定可能）。
- **プロンプト読み込み (`src/saint_graph/prompt_loader.py`)**:
  - **`PromptLoader`**: システム指示と、キャラクターの `system_prompts` ディレクトリにある Markdown テンプレートの読み込みを一元管理します。
  - **実装**: `pathlib.Path` を使用して動的にパスを解決し、環境に依存しない移植性の高い実装を実現しています。
- **設定可能なパラメータ (`src/saint_graph/config.py`)**:
  - `NEWS_DIR`: ニュース原稿ディレクトリ（デフォルト: `/app/data/news`）
  - `MAX_WAIT_CYCLES`: 沈黙タイムアウト秒数（デフォルト: `20`）
  - `MCP_URL`, `WEATHER_MCP_URL`: MCP サーバー接続先
- **システムプロンプト**:
  - **グローバル (`src/saint_graph/system_prompts/`)**:
    - `core_instructions.md`: 基本的なシステム指示とグローバルルール。
  - **キャラクター固有 (`src/mind/ren/system_prompts/`)**:
    - `intro.md`: Signature Greetings を使用した最初の挨拶。
    - `news_reading.md`: ニュース読み上げの指示（全文 + 解説）。
    - `news_finished.md`: ニュース終了後にフィードバックを求める指示。
    - `closing.md`: 配信終了の挨拶の指示。
    - `retry_*.md`: エラーハンドリング（ツール呼び出しの欠落など）のための再指示。
- **ループロジック**:
  0.  **自動録画の開始**: 配信開始の挨拶を行う前に `start_obs_recording` ツールを自動的に呼び出します。
  1.  **コメントのポーリング**: `_check_comments()` 経由で `body-cli` からのユーザー入力を確認します。
  2.  **ニュースの読み上げ**: コメントがない場合、`_run_newscaster_loop()` 経由で次のニュース項目を読み上げます。
  3.  **終了シーケンス**: 沈黙タイムアウト（`MAX_WAIT_CYCLES` で設定、デフォルト20秒）の後、終了シーケンスを開始します。

### 3.3 Saint Graph Agent (`src/saint_graph/saint_graph.py`)
- **ADK 統合**: `google.adk.Agent` をラップ。
- **ターン処理**: `process_turn(user_input, context)`
  - プロンプトにコンテキストを注入し、AI の振る舞いをガイドします。
  - **内部ヘルパー**:
    - `_is_tool_call(event, tool_name)`: ADK イベントストリーム内の特定のツール呼び出しを識別します。
    - `_detect_raw_text(event)`: エージェントがツール呼び出しの代わりに生テキストを出力したかどうかを検出します。
  - **再指示 (Retry Instruction) ロジック**:
    - `speak` ツールを使用せずに生テキストを出力した場合、またはユーザーへの最終回答なしにターンが終了した場合、AI に再指示を行います。

### 3.4 ペルソナ (`src/mind/ren/persona.md`)
- **キャラクター**: 紅月れん（わらわ/のじゃロリ系）。
- **口調**: 「わらわ」「のじゃ」「ぞい」の一貫した使用。
- **指示事項**:
  - **ニュース**: 本文をそのまま読み上げ、その後に個人的な意見を加える。
  - **交流**: キャラクターを維持してコメントに反応し、視聴者とのエンゲージメントを優先する。

## 4. 実装の詳細

### Docker 構成
- **ビルドコンテキスト**: `data/news` が利用可能であることを保証するため、`/app` ディレクトリ全体をコピーします。
- **ボリューム**: ビルド時の整合性を優先するため、`data` のボリュームマウントは現在無効化されています。
- **環境変数**: `PYTHONPATH=/app`, `GOOGLE_API_KEY` (必須)。

### 主な特徴
- **堅牢なニュース読み上げ**: タイトルだけでなく、本文全文が読み上げられることを保証します。
- **動的な交流**: 準備されたスクリプトよりもユーザーコメントを優先します。
- **スマートタイムアウト**: 終了フェーズ中にユーザーが交流した場合、セッション時間を動的に延長します。
- **キャラクターの一貫性**: システムプロンプトと Retry Instruction ロジックによって強制されます。

## 5. 使い方
1.  **起動**: `docker compose up --build`
2.  **交流**: `docker attach app-body-cli-1` を使用して、出力の確認とコメントの入力を行います。
3.  **ニュースの修正**: `data/news/news_script.md` を編集して、リビルド/再起動します。
