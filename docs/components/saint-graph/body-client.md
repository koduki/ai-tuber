# Body クライアント

Saint Graph から Body へ指令を送信する REST クライアントについて説明します。

---

## 役割

`body_client.py` は Body サービスへの HTTP リクエストをカプセル化し、シンプルな API を提供します。

---

## BodyClient クラス

### 初期化

```python
from saint_graph.body_client import BodyClient

# RUN_MODE に応じて自動的に URL が設定される
body_client = BodyClient(base_url=config.BODY_URL)
# CLI モード: http://body-cli:8000
# Streamer モード: http://body-streamer:8000
```

---

## メソッド

### speak(text, style)

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

**内部処理** (Streamer モード):
1. VoiceVox で音声合成
2. WAV ファイル保存
3. OBS で再生
4. 再生完了まで待機

### change_emotion(emotion)

アバターの表情を変更します。

```python
await body_client.change_emotion("joyful")
```

**パラメータ**:
- `emotion` (str): 感情（neutral, joyful, fun, angry, sad）

**内部処理** (Streamer モード):
- OBS のイメージソースを切り替え

### get_comments()

視聴者コメントを取得します。

```python
comments = await body_client.get_comments()
# CLI モード: ["コメント1", "コメント2"]
# Streamer モード: [{"author": "...", "message": "...", "timestamp": "..."}]
```

**戻り値**:
- CLI モード: `List[str]`
- Streamer モード: `List[Dict[str, str]]`

### start_recording() / stop_recording()

録画を開始・停止します（Streamer モードのみ）。

```python
# 録画開始
await body_client.start_recording()

# ... 配信処理 ...

# 録画停止
await body_client.stop_recording()
```

---

## 実装例

### 基本的な使用

```python
import asyncio
from saint_graph.body_client import BodyClient
from saint_graph.config import config

async def main():
    body_client = BodyClient(base_url=config.BODY_URL)
    
    # 挨拶
    await body_client.change_emotion("joyful")
    await body_client.speak("おはようございます！", style="joyful")
    
    # コメント確認
    comments = await body_client.get_comments()
    if comments:
        print(f"コメント: {comments}")

asyncio.run(main())
```

### エラーハンドリング

```python
import httpx

try:
    await body_client.speak("こんにちは")
except httpx.RequestError as e:
    logger.error(f"Body への接続エラー: {e}")
except httpx.HTTPStatusError as e:
    logger.error(f"Body がエラーを返しました: {e.response.status_code}")
```

---

## HTTP リクエストの詳細

### POST /api/speak

```python
# リクエスト
POST http://body-streamer:8000/api/speak
Content-Type: application/json

{
  "text": "こんにちは",
  "style": "joyful"
}

# レスポンス
{
  "status": "ok",
  "result": "発話完了"
}
```

### POST /api/change_emotion

```python
# リクエスト
POST http://body-streamer:8000/api/change_emotion
Content-Type: application/json

{
  "emotion": "joyful"
}

# レスポンス
{
  "status": "ok",
  "result": "表情を joyful に変更しました"
}
```

---

## 関連ドキュメント

- [README](./README.md) - Saint Graph 概要
- [通信プロトコル](../../architecture/communication.md) - REST API 仕様
- [Body](../../components/body/README.md) - Body 実装
