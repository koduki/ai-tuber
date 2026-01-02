# AI Tuber Modular Architecture (ADK + MCP)

このプロジェクトは、AI Tuber の機能を「Saint Graph (魂)」と「肉体（Body）」に分離したモジュール型アーキテクチャの MVP です。Google の **Agent Development Kit (ADK)** と **Model Context Protocol (MCP)** を活用しています。

## アーキテクチャ概要

システムは大きく3つの要素で構成されています：

1.  **Saint Graph (魂)**: `src/saint_graph/`
    *   **Gemini 2.0 Flash Lite** を搭載したエージェント。
    *   ADK を使用して、思考プロセスとツール実行を管理します。
    *   モジュール化された構造（`saint_graph.py`, `main.py`, `persona.py`, `tools.py`）により、保守性が向上しています。
2.  **Body (肉体/外部IF)**: `src/body/cli_tool/`
    *   **MCP Server** として実装されています。
    *   `speak`（発話）、`change_emotion`（表情変更）、`get_comments`（コメント取得）などのツールを提供します。
    *   現在は CLI モードで動作し、ターミナル上で対話が可能です。
3.  **Mind (人格)**: `src/mind/`
    *   キャラクターの性格、口調、行動指針を定義する `persona.md` を含みます。

詳細は [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) を参照してください。

## ディレクトリ構造

```text
/
├── src/
│   ├── body/            # MCP Server (Body) の実装
│   │   └── cli_tool/    # CLI用インターフェース
│   ├── mind/            # キャラクター設定 (Persona)
│   └── saint_graph/     # エージェントロジック (Saint Graph/魂)
│       ├── main.py      # Outer Loop / ライフサイクル管理
│       ├── saint_graph.py # Inner Loop / Saint Graph クラス
│       ├── persona.py   # Persona ロード処理
│       ├── tools.py     # ツール定義
│       ├── config.py    # 設定
│       └── mcp_client.py # Body接続用クライアント
├── .devcontainer/       # 開発環境設定
└── docker-compose.yml   # 実行環境定義
```

## 前提条件

*   Docker / Docker Compose
*   Google Gemini API Key

## セットアップ & 実行

### 1. 環境変数の設定
`.env` ファイルを作成してください。
```bash
GOOGLE_API_KEY=あなたのAPIキー
RUN_MODE=cli
```

### 2. システムの起動
```bash
docker-compose up
```
これにより、Saint Graph と Body の両方のコンテナが立ち上がります。

### 3. AI との会話
新しいターミナルを開き、Body コンテナにアタッチします。
```bash
docker attach ai-tuber-mcp-cli-1
```
ここでメッセージを入力すると、約10秒間隔の思考ループにより Saint Graph が反応を返します。

## 開発ガイド (DevContainer)

VS Code の **DevContainer** を使用すると、コンテナ内で直接 Saint Graph のコードを修正・再起動できます。

1. VS Code で開き、「Reopen in Container」を選択。
2. `saint-graph` ターミナルで実行：
   ```bash
   python3 -m src.saint_graph.main
   ```
3. ログを確認しながら、`src/` 配下のファイルを編集することでリアルタイムに挙動を変更できます。

## 技術スタック

*   **LLM**: Gemini 2.0 Flash Lite
*   **Agent Framework**: Google Agent Development Kit (ADK)
*   **Protocol**: Model Context Protocol (MCP)
*   **Language**: Python 3.11
*   **Infrastructure**: Docker / Docker Compose
