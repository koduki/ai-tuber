# コアロジック

Saint Graph の中核となる AI ターン処理と感情パース処理について説明します。

---

## Agent の初期化

### Google ADK 統合

Google ADK (Agent Development Kit) を使用して、LLM、ツール、および実行エンジンを統合します。

```python
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models import Gemini

# Body クライアントの初期化
# SaintGraph は外部から注入された BodyClient を使用します。
body = BodyClient(base_url=config.BODY_URL)

# MCP ツールセットの作成 (例)
# このツールセットは SaintGraph 内部で Agent に渡されます。
mcp_tools = McpToolset(server_urls=[config.MCP_URL])

# Agent の作成: ペルソナとツールの定義
agent = Agent(
    name="SaintGraph",
    model=Gemini(model="gemini-2.0-flash-exp"),
    instruction=system_instruction,
    tools=all_tools  # MCP Toolset + 外部注入ツールの結合
)

# Runner の作成: 実行エンジン
# InMemoryRunner は、対話履歴や中間状態をメモリ上で管理します。
runner = InMemoryRunner(agent=agent)

# SaintGraph の初期化 (BodyClient を渡す例)
sg = SaintGraph(
    body=body,
    mcp_url=config.MCP_URL,
    system_instruction=system_instruction,
    mind_config=mind_config
)
```

### ツール構成の設計

`SaintGraph` は、以下の2系統のツールを結合して `Agent` に提供します。

1.  **MCP Toolset (内部生成)**:
    - 実運用で使用する外部ツール。
    - `mcp_url` (SSE) 経由で動的に接続されます。
2.  **Custom Tools (外部注入)**:
    - `SaintGraph` 初期化時に `tools` 引数として渡されるツールのリスト。
    - **テストとモック**: 本物の MCP サーバーを起動せずにエージェントの挙動を検証するために使用。
    - **一時的な拡張**: MCP サーバー化するほどではない小規模な Python 機能を迅速に追加。

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

`process_turn()` メソッドは、`Runner` を介して AI とのやり取りを1ターン処理します。

---

## 配信ステートマシン (broadcast_loop.py)

### 概要

配信のライフサイクルは `broadcast_loop.py` の軽量ステートマシンで管理されます。
`BroadcastPhase` (Enum) と各フェーズのハンドラ関数で構成され、`main.py` から `run_broadcast_loop()` として呼び出されます。

### フェーズ遷移

```
INTRO → NEWS → (NEWS を繰り返し) → IDLE → (待機) → CLOSING → 終了
            ↑                         ↑
            コメント応答で留まる        コメント応答でカウンタリセット
```

### コメント処理の共通化

全フェーズのハンドラ冒頭で `_poll_and_respond()` を呼び出し、コメントが来ていれば優先的に応答します。これにより、ニュースの合間でも視聴者との対話が可能です。

```python
async def _poll_and_respond(ctx: BroadcastContext) -> bool:
    comments = await ctx.saint_graph.body.get_comments()
    if comments:
        await ctx.saint_graph.process_turn(formatted_comments)
        return True
    return False
```

### ディスパッチテーブル

```python
_HANDLERS = {
    BroadcastPhase.INTRO:   handle_intro,    # → NEWS
    BroadcastPhase.NEWS:    handle_news,     # → NEWS / IDLE
    BroadcastPhase.IDLE:    handle_idle,     # → IDLE / CLOSING
    BroadcastPhase.CLOSING: handle_closing,  # → None (終了)
}
```

### 拡張性

新しいフェーズを追加する場合は、`BroadcastPhase` に値を追加し、対応するハンドラ関数を `_HANDLERS` に登録するだけで対応できます。

### 処理フロー

#### 1. エージェントの実行

`runner.run_async` を使用して、セッション（履歴）を維持しながらエージェントを実行します。

```python
async for event in runner.run_async(
    new_message=types.Content(role="user", parts=[types.Part(text=user_input)]), 
    user_id="yt_user", 
    session_id="yt_session"
):
    # テキストパートを抽出して結合
    full_text += extract_text(event)
```

#### 2. レスポンスのパースと Body 連携

受信した `full_text` をセンテンス単位で分割し、感情タグに基づいて Body API を叩きます。

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
