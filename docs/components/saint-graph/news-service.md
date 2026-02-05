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
├── news_script.md     # ニュース原稿
└── (その他のファイル)
```

環境変数 `NEWS_DIR` でディレクトリを指定できます（デフォルト: `/app/data/news`）。

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
next_news = news_service.get_next_news()

if next_news:
    # AI に渡す
    prompt = f"次のニュースを読み上げてください:\n\nタイトル: {next_news.title}\n\n{next_news.content}"
    await agent.process_turn(prompt)
```

---

## メインループでの使用

```python
# ニュース読み上げフェーズ
while news_service.has_more_news():
    news = news_service.get_next_news()
    
    # AI に依頼
    prompt = f"次のニュースを解説してください:\n\n{news.title}\n{news.content}"
    await saint_graph.process_turn(prompt)
    
    # コメント取得・質疑応答
    await handle_comments()

# 全ニュース終了
print("すべてのニュース配信が完了しました")
```

---

## 関連ドキュメント

- [README](./README.md) - Saint Graph 概要
- [ニュース収集](./news-collector.md) - ニュースエージェント
- [コアロジック](./core-logic.md) - ターン処理
- [データフロー](../../architecture/data-flow.md) - 配信フロー
