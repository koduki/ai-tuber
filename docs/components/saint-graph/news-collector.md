# ニュース収集エージェント (News Collector Agent)

`news_agent.py` は、最新のニュースをウェブから収集し、AI Tuber 用のニュース原稿（Markdown形式）として出力するスタンドアロンのツールです。

---

## 主な機能

- **自律的検索**: Google Search（ADK GoogleSearchTool）を使用して、最新の話題を自律的に検索します。
- **特定日のニュース収集**: `--date` オプションにより、過去の特定の日付に関するニュースを収集可能です。
- **マルチテーマ対応**: デフォルトで以下のテーマをカバーしています：
    - 気になるアニメやVTuberの話題（スリム化・ジャンプ系除外済み）
    - 全国の天気予報
    - 経済指標（S&P500, 日経平均, 為替, ビットコイン, 金）
    - 経済・政治・テックニュース
- **高精度な原稿生成**: Gemini が検索結果を要約し、キャラクターが読み上げやすい自然な原稿を作成します。
- **ポストプロセス (Cleanup)**: 言い訳フレーズ（「見つかりませんでした」等）の除去や、重複出力の防止をプログラムレベルで行います。

---

## 使用方法

プロジェクトのルートディレクトリから実行します。

### 基本的な実行（今日のニュース）
```bash
python scripts/news_collector/news_agent.py
```

### テーマを指定して実行
テーマはパイプ (`|`) で区切ります。
```bash
python scripts/news_collector/news_agent.py --themes "全国の天気|最新のAIニュース"
```

### 日付を指定して実行 (YYYY-MM-DD)
```bash
python scripts/news_collector/news_agent.py --date 2024-02-04
```

---

## 実装の詳細

### 検索エンジン
従来の DuckDuckGo 検索から、より精度の高い **Google Search (ADK GoogleSearchTool)** に移行しました。これにより、Gemini が Grounding（根拠付け）を行いながら原稿を作成します。

### クリーンアップロジック (`clean_news_script`)
生成されたテキストに対して以下の処理を行います：
1. **Markdown コードブロックの除去**: 純粋なテキストのみを抽出。
2. **重複防止**: AI が誤って同じ内容を2回出力しても、最初の一つのみを採用。
3. **言い訳フレーズの除去**: 「検索しましたが...」「見つかりませんでした」等の、ニュース配信に不要なメタ発言を削除。

### サブカルセクションの制約
「気になるアニメやVTuberの話題」セクションには以下の制約がプロンプトで課せられています：
- **ジャンプ系除外**: 週刊少年ジャンプおよびその連載作品（ONE PIECE, 呪術廻戦等）の話題は含めない。
- **スリム化**: 全体の 1/3 程度の分量（1〜3項目）に抑える。

---

## 開発とテスト

### テストの実行
`clean_news_script` 関数の動作を検証するユニットテストが用意されています。
```bash
pytest tests/test_news_collector.py
```

### 依存関係
`scripts/news_collector/requirements.txt` に記載されています。
- `google-adk`
- `google-genai`
- `duckduckgo-search` (互換性のために残されていますが、現在は ADK Tool を推奨)
