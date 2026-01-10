# AI Tuber System Architecture

## 概要
本プロジェクトは、Google GenAI SDK (旧ADK) と Model Context Protocol (MCP) を活用した、モジュール構成のAI Tuberシステムです。
「Saint Graph (魂)」、「Mind (精神)」、「Body (肉体)」を明確に分離することで、拡張性と保守性を高めています。
詳細な仕様は `docs/specs/` 配下のドキュメントを参照してください。

## System Map

```mermaid
graph TD
  subgraph Mind ["Mind (精神)"]
    Persona["src/mind/{name}/persona.md"]
  end

  subgraph SaintGraph ["Saint Graph (魂)"]
    Gemini["Gemini Model"]
    Logic["main.py (Outer Loop)"]
    Soul["saint_graph.py (Inner Loop)"]
    Client["mcp_client.py"]
  end

  subgraph Body ["Body (肉体)"]
    Server["MCP Server"]
    CLI["CLI / View"]
  end

  Persona --> Logic
  Logic --> Soul
  Soul --> Client
  Client -- "MCP (JSON-RPC)" --> Server
  Server --> CLI
  CLI -- "User Input" --> Server
```

## Module Reference

各モジュールの詳細な仕様は以下のスペックファイルで定義されています。

### 1. Saint Graph (Brain/Soul)
*   **Role:** 対話制御、意思決定、コンテキスト管理
*   **Spec:** [docs/specs/saint-graph.md](./specs/saint-graph.md)
*   **Code:** `src/saint_graph/`

### 2. Body (Interaction Layer)
*   **Role:** 外部入出力（コメント取得、発話、表情制御）
*   **Interface Spec:** [docs/specs/api-design.md](./specs/api-design.md) (MCP Tools Definition)
*   **Implementation:** `src/body/` (Currently generic CLI implementation)
*   **Tech:** MCP Server (FastAPI + SSE)

### 3. Mind (Personality)
*   **Role:** キャラクター人格の定義
*   **Definition:** `src/mind/{character_name}/persona.md`
*   **Note:** `SaintGraph` 起動時にSystem Instructionとして読み込まれます。

### 4. Communication Channel
*   **Spec:** [docs/specs/mcp-client.md](./specs/mcp-client.md)
*   **Protocol:** HTTP + SSE (Server-Sent Events) for MCP

## Directory Structure Strategy

```text
.
├── agent.md             # Project Constitution & Rules
├── docs/
│   ├── ARCHITECTURE.md  # This Map
│   └── specs/           # Detailed Specifications (Source of Truth for implementation)
├── src/
│   ├── saint_graph/     # Core Logic (The Brain)
│   ├── body/            # Peripherals (The Body)
│   └── mind/            # Personality Data (The Mind)
```
