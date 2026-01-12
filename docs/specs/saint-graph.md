---
description: Application Implementation Specification for AI Newscaster
---

# Application Implementation Specification: Saint Graph AI Newscaster

## 1. Overview
The **Saint Graph AI Newscaster** is an automated, character-driven broadcasting system powered by an LLM (Gemini). It reads news scripts from Markdown files, adds persona-based commentary, and interacts with viewers via CLI. The system is containerized using Docker and leverages the Google Agent Development Kit (ADK).

## 2. Architecture
The system consists of three main Docker services:
- **`saint-graph`**: The core logic service.
  - Loads news from `data/news/news_script.md`.
  - Manages the AI persona ("Ren Kouzuki") and dialogue flow.
  - Connects to MCP servers (Weather, User Comments).
- **`body-cli`**: A CLI-based interface for outputting AI speech and accepting user comments.
- **`body-weather`**: A mock server providing weather data via MCP.

## 3. Core Components

### 3.1 News Service (`src/saint_graph/news_service.py`)
- **Functionality**: Parses `news_script.md` into `NewsItem` objects.
- **Format**: Supports Markdown with `## Title` headers.
- **Logic**:
  - `load_news()`: Reads file, splits by `##`, extracts title and body.
  - `get_next_item()`: Returns the next unread news item.
  - `has_next()`: Checks if more items exist.

### 3.2 Main Application Loop (`src/saint_graph/main.py`)
- **Initialization**:
  - Loads persona (`src/mind/ren/persona.md`).
  - Loads global instructions (`src/saint_graph/system_prompts/core_instructions.md`).
  - Loads character-specific templates from `src/mind/ren/system_prompts/`.
  - Initializes `SaintGraph` with MCP tools and Retry Instructions.
  - Loads news via `NewsService`.
- **System Prompts**:
  - **Global (`src/saint_graph/system_prompts/`)**:
    - `core_instructions.md`: Base system instructions and global rules.
  - **Character-Specific (`src/mind/ren/system_prompts/`)**:
    - `intro.md`: Initial greeting using Signature Greetings.
    - `news_reading.md`: Instructions for reading news (full text + commentary).
    - `news_finished.md`: Instructions for asking for feedback after news.
    - `closing.md`: Instructions for the final sign-off.
    - `retry_*.md`: Re-instructions for error handling (missing tool calls, etc.).
- **Loop Logic**:
  1.  **Poll for Comments**: Checks `body-cli` for user input (Priority 1).
      - If found, interrupts news flow to respond (`context="User Interaction"`).
      - Resets the "Silence Timeout" counter.
  2.  **Read News**: If no comments, reads the next news item (Priority 2).
      - **One-Shot Instruction**: Commands the AI to output Introduction + Body + Commentary in a single `speak` tool call.
      - **Context**: `News Reading: {Title}`.
  3.  **End Sequence**:
      - After all news is read, enters a "Waiting for Final Comments" state.
      - **Timeout**: If 20 seconds pass without interaction, initiates the Closing Sequence.
      - **Closing**: AI says a final farewell, waits 3 seconds, and the process terminates.

### 3.3 Saint Graph Agent (`src/saint_graph/saint_graph.py`)
- **ADK Integration**: Wraps `google.adk.Agent`.
- **Turn Processing**: `process_turn(user_input, context)`
  - Inject context into the prompt to guide AI behavior (e.g., "News Reading", "Closing").
  - **Retry Instruction Logic**:
    - Re-instructs the AI if it outputs raw text without using the `speak` tool, or if the turn terminates without a final response to the user. This ensures consistent tool usage regardless of the interaction mode.

### 3.4 Persona (`src/mind/ren/persona.md`)
- **Character**: Ren Kouzuki (Warawa/Noja-loli archetype).
- **Tone**: Consistent usage of "Warawa", "Noja", "Zoi".
- **Instructions**:
  - **News**: Read full content verbatim, then add personal opinion.
  - **Interaction**: Respond to comments in character, prioritize viewer engagement.

## 4. Implementation Details

### Docker Configuration
- **Build Context**: Copies full `/app` directory to ensure `data/news` is available.
- **Volumes**: Volume mounting for `data` is currently **disabled** to prioritize build-time consistency.
- **Environment**: `PYTHONPATH=/app`, `GOOGLE_API_KEY` (required).

### Key Features
- **Robust News Reading**: Ensures full body text is spoken, not just titles.
- **Dynamic Interaction**: Prioritizes user comments over prepared script.
- **Smart Timeout**: Extends session duration dynamically if users interact during the closing phase.
- **Character Consistency**: Enforced via system prompting and Retry Instruction logic.

## 5. Usage
1.  **Start**: `docker compose up --build`
2.  **Interact**: Use `docker attach app-body-cli-1` to see output and type comments.
3.  **Modify News**: Edit `data/news/news_script.md` and rebuild/restart.
