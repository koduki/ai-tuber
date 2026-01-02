# AI Tuber システムアーキテクチャ

## 概要

本プロジェクトは、Google Agent Development Kit (ADK) と Model Context Protocol (MCP) を活用した、モジュール構成のAI Tuberシステムです。
「思考（Saint Graph）」、「身体（Body）」、「記憶・人格（Mind）」を明確に分離することで、拡張性と保守性を高めています。

## アーキテクチャ図

```mermaid
graph TD
  subgraph Mind ["Mind (人格・記憶)"]
    Persona["src/mind/{name}/persona.md"]
  end

  subgraph SaintGraph ["Saint Graph (魂)"]
    Gemini["Gemini 2.0 Flash Lite"]
    ADK["Google ADK"]
    Logic["main.py (Outer Loop)"]
    Soul["saint_graph.py (Inner Loop)"]
    Client["mcp_client.py"]
  end

  subgraph Body ["Body (肉体・入出力)"]
    Server["MCP Server"]
    CLI["CLI / CLI View"]
    Obs["OBS (Future)"]
  end

  Persona --> Logic
  Gemini <--> ADK
  ADK --> Soul
  Logic --> Soul
  Soul --> Client
  Client -- "MCP (JSON-RPC)" --> Server
  Server --> CLI
  CLI -- "User Input" --> Server
```

## コンポーネント詳細

### 1. Saint Graph (魂)
- **パス**: `src/saint_graph/`
- **役割**: 思考、意思決定、行動の選択。
- **構成**:
    - `main.py`: **Outer Loop**。システム全体のライフサイクル管理、Bodyへの接続、ポーリングの制御を行います。
    - `saint_graph.py`: **Inner Loop**。`SaintGraph` クラスを含み、LLMとの対話履歴管理、ストリーミング応答の処理、ツール実行ループを担当します。
    - `persona.py`: Mindからキャラクター設定を読み込むローダー。
    - `tools.py`: LLMに提供するツール定義（`speak`, `change_emotion` 等）。
    - `config.py`: 環境変数や定数の管理。
    - `mcp_client.py`: Body (MCP Server) と通信するためのクライアント。
- **技術**: Google ADK, Gemini API (Gemini 2.0 Flash Lite), Python AsyncIO

### 2. Body (肉体)
- **パス**: `src/body/`
- **役割**: 外部世界とのインターフェース。音声出力、表情変更、コメント取得などの「能力」を提供します。
- **実装**: Model Context Protocol (MCP) サーバーとして実装されています。現在はCLIベースですが、将来的にはOBS連携やVTube Studio連携などの「異なる肉体」との連携を想定しています。
- **主要ファイル**:
    - `cli/main.py`: CLI版のBody実装。標準入力からのコメント受け取りや、標準出力への発話ログ表示を行います。

### 3. Mind (人格)
- **パス**: `src/mind/`
- **役割**: キャラクターの性格、口調、行動指針の定義。
- **主要ファイル**:
    - `{name}/persona.md`: キャラクターごとの定義ファイル（例：`ren/persona.md`）。プロンプトエンジニアリングにより、LLMの振る舞いを制御します。
    - `src/saint_graph/persona.py` の `load_persona(name)` 関数により、指定されたキャラクター名のディレクトリから厳密に読み込まれます。

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
    - Saint Graph (`main.py`) が `get_comments` ツールを定期的に呼び出します。
    - Body がユーザーからのコメント（標準入力など）を返します。

2. **思考 (Thinking)**:
    - Saint Graph (`saint_graph.py`) は観測結果と `persona.md` の内容を合わせて Gemini に送信します。
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

## 詳細実装: Body (CLI)

`src/body/cli/main.py` は、MCPサーバーとして動作するCLIアプリケーションです。
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

## 詳細解説: Saint Graph の実装と振る舞い

`src/saint_graph/` 配下の実装に基づく解析です。特に `main.py` の「Outer Loop」と `saint_graph.py` の「Inner Loop」の役割分担、および Gemini のストリーミング処理について詳述します。

### Outer Loop (ライフサイクル管理)
- **ファイル**: `src/saint_graph/main.py`
- **役割**: プロセス全体の監督。
- **振る舞い**:
  - `MCPClient` の接続確立と維持。
  - `SaintGraph` インスタンス（脳）の初期化。
  - 定期的な観測（`get_comments`）の実行と、自発的な発話（ソリロキュー）のトリガー管理。
  - ネットワークエラー等の例外を捕捉し、システムが停止しないようにリトライ制御を行います。

### Inner Loop (思考→行動ループ)
- **ファイル**: `src/saint_graph/saint_graph.py` (`SaintGraph` クラス)
- **役割**: 1回の対話ターンを完結させるための自律的な思考サイクル。
- **振る舞い**:
  - `process_turn(user_input)` が呼び出されると、ユーザー入力を履歴に追加し、Gemini へのリクエストを開始します。
  - このループは `while True:` で構成されており、Gemini が「ツール呼び出し（Function Calling）」を返し続ける限り、ループを継続します。
  - Gemini が発話（通常のテキスト応答）を返した場合、あるいはツール呼び出しがない場合にループを終了します。

### チャンクストリーミング (Chunk Streaming) の詳細

Google ADK を介した Gemini との通信には `model.generate_content_async(stream=True)` を使用しています。この非同期ストリーミング処理において、以下の点に注意して実装されています。

1.  **チャンクの蓄積**:
    - LLMからの応答は複数のチャンク（断片）に分割されて届きます。
    - 単一のチャンク（特に最後のチャンク）だけを参照すると、生成されたテキストや関数呼び出しの引数が不完全になる可能性があります。
    - そのため、ループ内で `accum_parts`（Content Partのリスト）と `accum_text`（テキスト全文）に全てのチャンクの内容を累積させています。

2.  **リアルタイムログ出力**:
    - 累積された `accum_text` の長さを前回の出力時と比較し、増分（差分）だけをログに出力しています。
    - これにより、ユーザーはAIが思考・発話している様子をリアルタイムに確認できます。

3.  **Function Calling の扱い**:
    - ストリーミングが完了した時点で、蓄積された `final_content` の `parts` を検査します。
    - `function_call` が含まれている場合、引数（args）を正規化（JSONパース等）した上でツールを実行します。
    - 実行結果（またはエラー）は `FunctionResponse` として履歴に追加され、次回の Gemini への入力としてフィードバックされます。
