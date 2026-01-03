# AI Tuber (Architecture Refactored)

This project explores the construction of an AI Agent using the Model Context Protocol (MCP) and Google's Agent Development Kit (ADK).

## Architecture: "Saint Graph" & "Single Body"

The architecture is simplified into a central reasoning engine (Saint Graph) and a single capability provider (Body).

*   **Saint Graph (The Spirit)**:
    *   **Outer Loop (`src/saint_graph/main.py`)**: Manages the application lifecycle, connects to the MCP Body, and runs the "News Loop".
    *   **Inner Loop (`src/saint_graph/saint_graph.py`)**: Handles the LLM interaction (Turn-based conversation). It generates content, executes tools, and loops until the model is satisfied.
    *   **Mind (`src/mind`)**: Stores the persona/system instructions.
    *   **MCP Client (`src/saint_graph/mcp_client.py`)**: A forward-compatible client that connects to a single MCP server. It implements standard `list_tools` and `call_tool` methods.

*   **Body (The Capabilities)**:
    *   **MCP Server (e.g., `src/body/cli`)**: Provides tools and I/O capabilities. Saint Graph connects to this single endpoint.

## Getting Started

### Prerequisites

*   Docker & Docker Compose
*   Google Gemini API Key

### Configuration

Set your API key in `.env` or environment variables:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### Running (Development)

The project includes a `devcontainer` configuration. Open the folder in VS Code with "Reopen in Container".

Or run manually:

```bash
docker-compose up --build
```

### Key Concepts

*   **Single Connection**: Saint Graph connects to one MCP endpoint (defined by `MCP_URL`).
*   **Standardized Interface**: The `MCPClient` is designed to mirror the official Python SDK's `ClientSession` interface (`list_tools`, `call_tool`), facilitating future migration.
