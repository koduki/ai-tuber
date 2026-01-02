# AI Tuber システムアーキテクチャ

## 概要

本プロジェクトは、Google Agent Development Kit (ADK) と Model Context Protocol (MCP) を活用した、モジュール構成のAI Tuberシステムです。
「思考（Saint Graph）」、「身体（Body）」、「記憶・人格（Mind）」を明確に分離することで、拡張性と保守性を高めています。

## アーキテクチャ図

```mermaid
graph TD
  subgraph Mind ["Mind (人格・記憶)"]
    Persona["persona.md"]
  end

  subgraph SaintGraph ["Saint Graph (魂)"]
    Gemini["Gemini 2.0 Flash Lite"]
    ADK["Google ADK"]
    Logic["main.py"]
    Client["mcp_client.py"]
  end

  subgraph Body ["Body (肉体・入出力)"]
    Server["MCP Server"]
    CLI["CLI Tool / CLI View"]
    Obs["OBS (Future)"]
  end

  Persona --> Logic
  Gemini <--> ADK
  ADK --> Logic
  Logic --> Client
  Client -- "MCP (JSON-RPC)" --> Server
  Server --> CLI
  CLI -- "User Input" --> Server
```

## コンポーネント詳細

### 1. Saint Graph (魂)
- **パス**: `src/saint_graph/`
- **役割**: 思考、意思決定、行動の選択。
- **主要ファイル**:
    - `main.py`: メインの思考ループ。`get_comments` で状況を観測し、LLMにコンテキストを与え、適切なツール（`speak`, `change_emotion` 等）を実行します。
    - `mcp_client.py`: Body (MCP Server) と通信するためのクライアント。
- **技術**: Google ADK, Gemini API (Gemini 2.0 Flash Lite), Python AsyncIO

### 2. Body (肉体)
- **パス**: `src/body/`
- **役割**: 外部世界とのインターフェース。音声出力、表情変更、コメント取得などの「能力」を提供します。
- **実装**: Model Context Protocol (MCP) サーバーとして実装されています。現在はCLIベースですが、将来的にはOBS連携やVTube Studio連携などの「異なる肉体」との連携を想定しています。
- **主要ファイル**:
    - `cli_tool/main.py`: CLI版のBody実装。標準入力からのコメント受け取りや、標準出力への発話ログ表示を行います。

### 3. Mind (人格)
- **パス**: `src/mind/`
- **役割**: キャラクターの性格、口調、行動指針の定義。
- **主要ファイル**:
    - `ren/persona.md`: 「紅月れん」というキャラクターの定義ファイル。プロンプトエンジニアリングにより、LLMの振る舞いを制御します。

## Google Agent Development Kit (ADK) について

Google ADK は、生成AIエージェントを構築するためのフレームワークです。
本プロジェクトでは、`src/saint_graph/` において以下の目的で使用しています。

1.  **モデル抽象化**:
    - `google.adk.models.Gemini` クラスを使用し、Gemini API への接続を簡潔に記述しています。
    - モデルの初期化や設定（Temperatureなど）を統一的に管理します。

2.  **ツール定義の標準化**:
    - `google.genai.types` を用いて、関数（ツール）の定義（名前、説明、引数スキーマ）を行います。
    - これにより、LLMに対して「何ができるか」を明確に伝え、Function Calling の精度を向上させています。

3.  **対話履歴の管理**:
    - エージェントのコンテキスト（過去のやり取り）を管理し、継続的な対話をサポートします。

従来の素のAPIコールに比べ、エージェント特有のループ（観測→思考→行動）の実装が容易になり、コードの可読性が向上しています。

## データフロー

1. **観測 (Observation)**:
    - Saint Graph が `get_comments` ツールを呼び出します。
    - Body がユーザーからのコメント（標準入力など）を返します。

2. **思考 (Thinking)**:
    - Saint Graph は観測結果と `persona.md` の内容を合わせて Gemini に送信します。
    - Gemini は状況に応じて、発話 (`speak`) や表情変更 (`change_emotion`) などのツール呼び出しを決定します。

3. **行動 (Action)**:
    - Saint Graph が決定されたツールを Body (MCP Server) に対して実行要求します。
    - Body が実際にアクション（ログ出力など）を行います。

## 技術スタック

- **LLM**: Gemini 2.0 Flash Lite
- **Agent Framework**: Google Agent Development Kit (ADK)
- **Protocol**: Model Context Protocol (MCP) - コンポーネント間の疎結合な通信を実現
- **Language**: Python 3.11
- **Container**: Docker / Docker Compose

## 詳細実装: Body (CLI Tool)

`src/body/cli_tool/main.py` は、MCPサーバーとして動作するCLIアプリケーションです。
主な実装ポイントを以下に解説します。

### 1. 入力処理 (Input Handling)

ユーザーからの入力（標準入力）をノンブロッキングで処理するため、別スレッドで読み込みを行い、Queueに格納しています。

```python
# input_queue に入力を溜める
input_queue = Queue()

def stdin_reader():
    """標準入力を読み込み、Queueに追加するスレッド"""
    while True:
        try:
            line = sys.stdin.readline()
            if line:
                input_queue.put(line.strip())
        except Exception:
            break

# デーモンスレッドとして起動
threading.Thread(target=stdin_reader, daemon=True).start()
```

### 2. ツール実装 (Tools Implementation)

LLMが実行する実際の関数です。CLI版では `print` 文で動作をシミュレートしています。

```python
async def speak(text: str, style: Optional[str] = None):
    """発話機能"""
    style_str = f" ({style})" if style else ""
    print(f"\n[AI{style_str}]: {text}")
    return "Speaking completed"

async def change_emotion(emotion: str):
    """表情変更"""
    print(f"\n[Expression]: {emotion}")
    return "Emotion changed"
```

### 3. MCP エンドポイント

FastAPI を使用して、MCP プロトコルに必要なエンドポイントを提供しています。

- **GET /sse**: Server-Sent Events (SSE) による接続確立。
- **POST /messages**: JSON-RPC によるリクエスト処理（ツール実行など）。

```python
@app.post("/messages")
async def handle_messages(request: Request):
    """JSON-RPC メッセージの処理"""
    data = await request.json()
    method = data.get("method")

    # ツール一覧の要求
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "result": { "tools": TOOL_DEFINITIONS },
            "id": data.get("id")
        }

    # ツールの実行
    if method == "tools/call":
        # ... (ツール名と引数を取得して実行) ...
```

## 詳細解説: src/saint_graph/main.py の二重ループとチャンクストリーミングの振る舞い

以下は `src/saint_graph/main.py`（commit 9ce7adb3） の実装に基づく正確な解析と運用上の注記です。特に `main()` 内にある「外側（監督）ループ」と「内側（思考/行動）ループ」、および Gemini のストリーミング応答（チャンク）周りの処理を詳述します。

### 外側ループ（監督ループ）
- 役割: プロセス全体のライフサイクルを管理し、MCP クライアントの接続やリトライ、例外発生時の待機などを担います。
- 実装上の振る舞い:
  - `while True:` でプロセスを継続させ、`get_comments` のポーリングやソリロキュー（無入力時の自発的発話）を管理します。
  - ネットワーク等の一時的エラーが発生した場合は例外を捕捉して `await asyncio.sleep(5)` で待機後に再試行します。
  - 内側ループを抜ける（例: 致命的エラーや接続喪失）と、外側で再初期化やクリーンアップを試みる設計になっています。

### 内側ループ（思考→行動ループ、Soul cycle）
- 役割: 1サイクルごとに観測を受け、LLM に文脈を送り、生成された応答を処理（ツール呼び出し等）します。
- 実装のポイント:
  - 観測（`get_comments`）を元に `chat_history` を更新し、LLM に送る `LlmRequest` を構築します。
  - 内側で `while True:` を回すのは、LLM がツール呼び出し（function_call）を返し、その実行結果をフィードバックしてさらに追加のツール呼び出しやテキスト生成が必要かを継続的に処理するためです。
  - この内側ループは、LLM の応答が「ツール呼び出しを含む限り」継続し、ツール呼び出しが無くなった段階で break して内側ループを終了します。

### llm_request が二回代入されている理由（コード上の事実と判断）
- 元の実装では外側で一度 `llm_request` を作成した直後、内側ループ開始直前で再生成して上書きしていました。現状は二度目が有効で最初の代入は使われていないため冗長と判断しました。
- 推奨: テンプレートを残すなら `base_request` を用意して内側ループでコピーするか、不要なら最初の代入を削除すること。

### チャンクストリーミング（model.generate_content_async の扱い）
- 各チャンクの parts を逐次累積して最終的に統合する実装にする必要があります（最終チャンクだけに依存すると text や function_call を取りこぼす場合があるため）。
- 差分ログは「累積テキスト」に対して printed_len を比較して出力するのが安全です。
- function_call の args は文字列(JSON)かオブジェクトか両方の可能性があるため、呼び出し前に正規化（json.loads を試す等）し、ツール実行失敗時のエラーを履歴に含めて LLM にフィードバックする。

### 推奨修正点（まとめ）
1. `llm_request` の重複代入を解消し、テンプレートを明示する（`base_request` を導入）。
2. ストリーミングは累積バッファ（parts/text）を用いて最終 content を構築する。
3. `fc.args` の正規化とツール実行失敗時のエラーを `FunctionResponse` として履歴に追加する。
4. 単体/統合テストで複数チャンク・複数 function_call のシナリオを検証する。

（既存の詳細は本ファイルに保持しています）
