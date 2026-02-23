# Body クライアント

Saint Graph から Body へ指令を送信する REST クライアントについて説明します。

---

## 役割

`body_client.py` は Body サービスへの HTTP リクエストをカプセル化し、シンプルな API を提供します。
内部的に共通の `_request` メソッドを使用することで、通信処理とエラーハンドリングを一元管理しています。

---

## BodyClient クラス

### 初期化

```python
from saint_graph.body_client import BodyClient

# RUN_MODE に応じて自動的に URL が設定される
body_client = BodyClient(base_url=config.BODY_URL)
# CLI モード: http://body-cli:8000
# Streamer モード: http://body-streamer:8002
```

---

## メソッド

### speak(text, style, speaker_id=None)

テキストを発話させます。

```python
await body_client.speak(
    text="こんにちは、今日は良い天気ですね！",
    style="joyful"
)
```

**パラメータ**:
- `text` (str): 発話させるテキスト
- `style` (str): 発話スタイル（neutral, joyful, fun, angry, sad）
- `speaker_id` (int, Optional): 声の ID（style より優先）

**内部処理** (Streamer モード):
1. リクエストを送信し、Body 側で内部キューに追加
2. キューにより、前後の発話や表情変更と順次実行される
3. **非ブロッキング**: 本メソッドはキューへの追加が完了した時点で即時復帰します（Mind 側で待機する必要がありません）。

### change_emotion(emotion)

アバターの表情を変更します。

```python
await body_client.change_emotion("joyful")
```

**パラメータ**:
- `emotion` (str): 感情（neutral, joyful, fun, angry, sad）

**内部処理** (Streamer モード):
- 表情変更リクエストを内部キューに追加し、発話と同期して順次処理されます。

### get_comments()

視聴者コメントを取得します。

```python
comments = await body_client.get_comments()
# [{"author": "...", "message": "...", "timestamp": "..."}]
```

**戻り値**:
- `List[Dict[str, Any]]`: コメントのリスト。CLI モードでも Streamer モードと互換性のある形式で返されます。

### start_broadcast(config) / stop_broadcast()

配信または録画を開始・停止します。

```python
# 配信開始
await body_client.start_broadcast({"title": "Live Stream"})

# ... 配信処理 ...

# 配信停止
await body_client.stop_broadcast()
```

- **概要**: 録画と配信を統合したエンドポイントです。環境変数 `STREAMING_MODE` に基づき、Body 側で自動的に OBS 録画か YouTube Live 配信かを判定します。
- **補足**: `stop_broadcast` は、キュー内のすべての発話が完了するのを待機してから停止処理を行いますが、呼び出し側でも必要に応じて `wait_for_queue` を使用できます。

### wait_for_queue(timeout=300.0)

キュー内のすべての処理（発話、表情変更）が完了するまで待機します。

```python
await body_client.wait_for_queue()
```

- **用途**: 配信のリズムを整えるために、1つのフェーズやターンが終わる際に AI が最後まで話し終えるのを待つために使用します。通信による「間」を詰めつつ、対話のリズムを維持するための「いいとこ取り」構成の要となります。

---

## 設計の詳細

### 共通リクエスト処理 (`_request`)

`BodyClient` 内部では、重複を避けるために共通のプライベートメソッドを使用しています。

```python
async def _request(self, method, path, payload=None, timeout=DEFAULT_TIMEOUT):
    # httpx.AsyncClient による送信と共通のエラーハンドリング
    ...
```

### エラーハンドリング

`BodyClient` の各メソッドは内部で例外をキャッチし、エラー発生時は "Error: ..." という文字列を返すか、空のリストを返します。呼び出し側の `Mind` ロジックが通信エラーによってクラッシュするのを防いでいます。

---

## 関連ドキュメント

- [README](./README.md) - Saint Graph 概要
- [通信プロトコル](../../architecture/communication.md) - REST API 仕様
- [Body](../../components/body/README.md) - Body 実装
