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

## トラブルシューティング
- **429 RESOURCE_EXHAUSTED**: APIのレート制限です。Gemini Experimentalモデルなどは制限が厳しいため、少し待つか `src/saint_graph/main.py` の待機時間を延ばしてください。
- **404 NOT_FOUND**: モデル名が間違っているか、キーでそのモデルが使えません。
- **反応がない**: `docker attach` しているか確認してください。ログに `User Comments: No new comments` と出続けている場合、入力が届いていません。
