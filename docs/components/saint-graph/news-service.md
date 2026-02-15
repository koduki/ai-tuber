# ニュース配信サービス

Saint Graph のニュース原稿管理と配信制御について説明します。

---

## 役割

`news_service.py` は Markdown 形式のニュース原稿を読み込み、配信管理を行います。原稿の自動生成については [ニュース収集エージェント](./news-collector.md) を参照してください。

---

## ニュース原稿フォーマット

### ディレクトリ構成

```
data/news/
├── news_script.md     # ニュース原稿（ローカル）
└── (その他のファイル)
```

環境変数 `NEWS_DIR` でディレクトリを指定できます（デフォルト: `/app/data/news`）。

### ストレージ連携
 
GCP 環境では、ニュース原稿を **Cloud Storage** から取得します。ローカル開発環境ではプロジェクトの `data/` ディレクトリから読み込みます。
 
**特長**:
- **透過的なアクセス**: `StorageClient` が環境変数 `STORAGE_TYPE` に応じて自動的に物理的な場所（GCS バケットかローカル FS か）を切り替えます。
- **デフォルトバケット**: `GCS_BUCKET_NAME` が設定されている場合、利用側コードでバケット名を指定する必要はありません。
 
**環境変数**:
```bash
STORAGE_TYPE=gcs                # または filesystem
GCS_BUCKET_NAME=ai-tuber-news  # GCS バケット名
NEWS_DIR=news                   # 論理パス（デフォルト）
```
 
この仕組みにより、Saint Graph はインフラの詳細を知ることなく、常に `news/news_script.md` という論理的なキーで最新の原稿にアクセスできます。

### Markdown フォーマット

```markdown
## ニュースタイトル1

ニュース本文

##  ニュースタイトル2

ニュース本文...
```

**ルール**:
- `## ` で始まる行がニュースタイトル
- その下の本文が1つの NewsItem になる

---

## NewsItem クラス

```python
@dataclass
class NewsItem:
    title: str
    content: str
```

### 使用例

```python
item = NewsItem(
    title="天気予報",
    content="今日は全国的に高気圧に覆われ..."
)
```

---

## NewsService クラス

### 初期化

```python
from saint_graph.news_service import NewsService

news_service = NewsService(news_dir="/app/data/news")
```

### ニュース読み込み

```python
# news_script.md を読み込み
news_items = news_service.load_news()
# → List[NewsItem]
```

### 配信管理

```python
# 次のニュースを取得
next_news = news_service.get_next_item()

if next_news:
    # SaintGraph の高レベルメソッドに委譲（テンプレート適用は AI 側で実施）
    await saint_graph.process_news_reading(title=next_news.title, content=next_news.content)
```

---

## メインループでの使用

```python
# ニュース読み上げフェーズ (broadcast_loop.py 内のイメージ)
while news_service.has_next():
    news = news_service.get_next_item()
    
    # AI に依頼（高レベルメソッドの呼び出し）
    await saint_graph.process_news_reading(title=news.title, content=news.content)
    
    # コメント取得・質疑応答
    await _poll_and_respond(ctx)

# 全ニュース終了
await saint_graph.process_news_finished()
```

---

## 関連ドキュメント

- [README](./README.md) - Saint Graph 概要
- [ニュース収集](./news-collector.md) - ニュースエージェント
- [コアロジック](./core-logic.md) - ターン処理
- [データフロー](../../architecture/data-flow.md) - 配信フロー
