# AI Tuber システムアーキテクチャ

## 概要

本プロジェクトは、Google Agent Development Kit (ADK) と Model Context Protocol (MCP) を活用した、モジュール構成のAI Tuberシステムです。
「思考（Saint Graph）」、「身体（Body）」、「記憶・人格（Mind）」を明確に分離することで、拡張性と保守性を高めています。

## アーキテクチャ図

```mermaid
graph TD
    subgraph Mind ["Mind (人格・記憶)"]
        Persona[persona.md]
    end

    subgraph SaintGraph ["Saint Graph (魂)"]
        Gemini[Gemini 2.0 Flash Lite]
        ADK[Google ADK]
        Logic[main.py]
        Client[mcp_client.py]
    end

    subgraph Body ["Body (肉体・入出力)"]
        Server[MCP Server]
        CLI[CLI Tool / CLI View]
        Obs[OBS (Future)]
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
- **実装**: Model Context Protocol (MCP) サーバーとして実装されています。現在はCLIベースですが、将来的にはOBS連携やVTube Studio連携などの「異なる肉体」への差し替えが容易な設計です。
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
