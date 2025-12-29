# AI Tuber Modular MVP (CLI Mode)

AI TuberのModular MVP（CLI Body版）です。
Brain（Gemini）とBody（MCP Server）が分離した設計になっています。
現在は開発用モードとして、ターミナルで会話が可能です。

## 前提条件
- Docker Desktop がインストールされていること
- Google Gemini API Key を持っていること

## セットアップ

1. **環境変数の設定**
   `.env` ファイルをプロジェクトルートに作成し、APIキーを設定してください。
   ```bash
   GOOGLE_API_KEY=AIzr...
   RUN_MODE=cli
   ```

2. **ビルド**
   ```powershell
   docker-compose build
   ```

## 起動と会話の方法

このシステムは2つのターミナルウィンドウを使用します。
1つは**システムの起動ログ用**、もう1つは**AIへの入力（会話）用**です。

### 手順 1: システムの起動
ターミナルを開き、以下のコマンドでシステムを起動します。
```powershell
docker-compose up
```
ログが表示され、システムが動き出します（Brainが定期的に周囲を確認し始めます）。
このターミナルはそのままにしておいてください。

### 手順 2: 会話への参加（入力）
**新しいターミナルウィンドウ**を開き、以下のコマンドを実行してBody（肉体）に接続します。
```powershell
docker attach ai-tuber-mcp-cli-1
```

### 手順 3: 会話する
接続したターミナルで、AIにかけたい言葉を入力して **Enter** を押してください。
（※入力プロンプトは表示されませんが、入力は受け付けられています）

例:
```text
こんにちは！
```

しばらく待つと（約10秒間隔）、AIが反応し、手順1（または手順2）のログに以下のように表示されます。

```text
[Expression]: happy
[AI (happy)]: こんにちは！今日も元気？
```

### 終了方法
`docker-compose up` を実行したターミナルで `Ctrl+C` を押して終了してください。

## DevContainer での開発方法

VS Code の DevContainer を使用すると、依存関係がインストール済みの環境ですぐに開発を開始できます。

### 1. DevContainer の起動
1. VS Code でプロジェクトを開きます。
2. 「Reopen in Container」を選択してコンテナを起動します。

### 2. Brain の起動（コンテナ内ターミナル）
DevContainer 内のターミナル（`saint-graph` コンテナ）で、思考エンジンを起動します。
```bash
# 環境変数の確認
export GOOGLE_API_KEY="your_api_key_here"

# 実行
python3 src/saint_graph/main.py
```

### 3. Body への接続（ホスト側ターミナル）
開発コンテナ内からは他のコンテナに `attach` できないため、**ホストマシン（Windows/Mac/Linux）のターミナル**から実行します。
```bash
docker attach ai-tuber-mcp-cli-1
```
ここに文字を入力することで、コンテナ内で動いている Brain にコメントを送信できます。

### 4. ログの確認
- **Brain の思考プロセス**: VS Code のターミナル（`saint-graph`）に表示されます。
- **Body の出力（発話・表情）**: `docker attach` しているホスト側のターミナル、または `docker compose logs -f mcp-cli` で確認できます。

## トラブルシューティング
- **429 RESOURCE_EXHAUSTED**: APIのレート制限です。Gemini Experimentalモデルなどは制限が厳しいため、少し待つか `src/saint_graph/main.py` の待機時間を延ばしてください。
- **404 NOT_FOUND**: モデル名が間違っているか、キーでそのモデルが使えません。
- **反応がない**: `docker attach` しているか確認してください。ログに `User Comments: No new comments` と出続けている場合、入力が届いていません。
