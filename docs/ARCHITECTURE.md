# AI Tuber システムアーキテクチャ

## 概要

本プロジェクトは、Google Agent Development Kit (ADK) と Model Context Protocol (MCP) を活用した、モジュール構成のAI Tuberシステムです。
「思考（Soul）」、「身体（Body）」、「記憶・人格（Mind）」を明確に分離することで、拡張性と保守性を高めています。

## アーキテクチャ図

```mermaid
graph TD
    subgraph Mind ["Mind (人格・記憶)"]
        Persona[persona.md]
    end

    subgraph Soul ["Saint Graph (魂)"]
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
