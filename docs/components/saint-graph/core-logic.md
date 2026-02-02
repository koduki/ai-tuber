# コアロジック

Saint Graph の中核となる AI ターン処理と感情パース処理について説明します。

---

## Agent の初期化

### Google ADK 統合

```python
from google.genai import Client
from google.adk import Agent
from google.adk.tools import McpToolset

# Gemini クライアント
client = Client(api_key=config.GOOGLE_API_KEY)

# MCP ツールセットの作成
tools = McpToolset(server_urls=[config.WEATHER_MCP_URL])

# Agent の作成
agent = Agent(
    model=config.MODEL_NAME,
    system_instruction=combined_prompt,  # システム + キャラクタープロンプト
    tools=tools
)
```

### プロンプトの結合

```python
# システムプロンプト（共通）
system_prompt = load_system_prompts(phase="intro")

# キャラクタープロンプト（個性）
character_prompt = load_character_prompt(character_name)

# 結合
combined_prompt = f"{system_prompt}\n\n{character_prompt}"
```

---

## ターン処理 (process_turn)

### 概要

`process_turn()` メソッドは AI とのやり取りを1ターン処理します。

**入力**: ユーザー入力（ニュース原稿 or 視聴者コメント）  
**出力**: なし（Body への指令送信が完了）

### 処理フロー

#### 1. AI にユーザー入力を送信

```python
async def process_turn(user_input: str) -> None:
    # AI にメッセージを送る
    response = await agent.send_message_async(user_input)
```

#### 2. ストリーミングレスポンスの受信

```python
    # AI からの応答をストリーミングで受信
    full_text = ""
    async for chunk in response:
        if chunk.text:
            full_text += chunk.text
```

#### 3. センテンス分割

```python
    # 文単位で分割（。！？.!?）
    import re
    sentences = re.split(r'([。！？.!?]+)', full_text)
    
    # 区切り文字を元に戻す
    combined_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i] + sentences[i + 1]
        if sentence.strip():
            combined_sentences.append(sentence)
```

#### 4. 各センテンスの処理（順次実行）

```python
    previous_emotion = None
    
    for sentence in combined_sentences:
        # 感情タグのパース
        emotion, text = parse_emotion_tag(sentence)
        
        # 感情変更（必要な場合）
        if emotion and emotion != previous_emotion:
            await body_client.change_emotion(emotion)
            previous_emotion = emotion
        
        # 発話（再生完了まで待機）
        if text.strip():
            await body_client.speak(text, style=emotion or "neutral")
```

---

## 感情パース処理

### 感情タグの形式

```
[emotion: neutral] テキスト内容
```

**対応する感情**:
- `neutral` - 通常
- `joyful` - 喜び
- `fun` - 楽しい
- `sad` - 悲しい
- `angry` - 怒り

### パース関数

```python
import re

def parse_emotion_tag(text: str) -> tuple[str | None, str]:
    """
    感情タグをパースする
    
    Args:
        text: "[emotion: joyful] こんにちは！"
    
    Returns:
        (emotion, clean_text): ("joyful", "こんにちは！")
    """
    pattern = r'\[emotion:\s*(\w+)\]\s*'
    match = re.search(pattern, text)
    
    if match:
        emotion = match.group(1)
        clean_text = re.sub(pattern, '', text)
        return emotion, clean_text.strip()
    
    return None, text.strip()
```

### 使用例

```python
# AI レスポンス
response = "[emotion: joyful] 皆の衆、おはのじゃ！"

# パース
emotion, text = parse_emotion_tag(response)
# emotion = "joyful"
# text = "皆の衆、おはのじゃ！"

# Body に指令
await body_client.change_emotion("joyful")
await body_client.speak("皆の衆、おはのじゃ！", style="joyful")
```

---

## セッション管理

### セッションの開始

```python
# Agent のセッション開始
session = agent.start_session()
```

### メッセージ履歴

ADK Agent は自動的にメッセージ履歴を管理します。

```python
# 1ターン目
await agent.send_message_async("こんにちは")

# 2ターン目（前のコンテキストを保持）
await agent.send_message_async("天気を教えて")
# → Agent は「こんにちは」のコンテキストを覚えている
```

### セッションのリセット

```python
# 新しいセッションを開始（履歴をクリア）
session = agent.start_session()
```

---

## センテンス順次再生の保証

### 問題点

以前のバージョンでは、長文の音声が途中で次の音声に上書きされる問題がありました。

### 解決策

センテンス単位で音声生成→再生→完了待機を順次実行することで、音声の重複を完全に防止します。

```python
for sentence in sentences:
    emotion, text = parse_emotion_tag(sentence)
    
    # 感情変更
    if emotion != previous_emotion:
        await body_client.change_emotion(emotion)
    
    # 発話（★ ここで再生完了まで待機 ★）
    await body_client.speak(text, style=emotion)
    # → Body 側で再生時間を計算して待機
    
    # 次のセンテンスへ（前の音声が完了している）
```

---

## エラーハンドリング

### Body との接続エラー

```python
try:
    await body_client.speak(text)
except httpx.RequestError as e:
    logger.error(f"Body への接続エラー: {e}")
    # 再試行または終了
```

### AI レスポンスのパースエラー

```python
try:
    emotion, text = parse_emotion_tag(sentence)
except Exception as e:
    logger.warning(f"感情パースエラー: {e}")
    # デフォルト感情で続行
    emotion = "neutral"
```

---

## 設計の意図

### なぜテキストベースのパースか？

**以前の方式**: AI に `speak` ツールを呼び出させる  
**問題点**:
- AI がツールを呼び忘れることがある
- ツール呼び出しの失敗がある
- 発話順序の制御が難しい

**現在の方式**: 生成テキストから感情タグをパース  
**メリット**:
- AI は自然なテキスト生成に集中できる
- 感情抽出が確実
- 発話順序を完全に制御できる

### なぜセンテンス単位か？

- 長文の一括再生だと音声が重複する
- センテンス単位なら感情の切り替えがスムーズ
- 視聴者が聞き取りやすい

---

## 関連ドキュメント

- [README](./README.md) - Saint Graph 概要
- [ニュース配信](./news-service.md) - ニュース管理
- [Body クライアント](./body-client.md) - REST クライアント実装
- [データフロー](../../architecture/data-flow.md) - 処理シーケンス
