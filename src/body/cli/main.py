import asyncio
import sys
import json
import threading
from typing import List, Optional
from queue import Queue, Empty

from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

# --- I/O Abstraction ---
class IOAdapter:
    def __init__(self):
        self._input_queue = Queue()

    def write_output(self, text: str):
        print(text)

    def add_input(self, text: str):
        self._input_queue.put(text)

    def get_inputs(self) -> List[str]:
        inputs = []
        while not self._input_queue.empty():
            try:
                inputs.append(self._input_queue.get_nowait())
            except Empty:
                break
        return inputs

io_adapter = IOAdapter()

def stdin_reader():
    """Reads lines from stdin and puts them in a queue."""
    sys.stderr.write("DEBUG: Starting stdin_reader thread\n")
    while True:
        try:
            line = sys.stdin.readline()
            if line:
                io_adapter.add_input(line.strip())
        except Exception as e:
            sys.stderr.write(f"Error reading stdin: {e}\n")
            break

# Start stdin reader in background
threading.Thread(target=stdin_reader, daemon=True).start()

# --- Tools Implementation ---

async def speak(text: str, style: Optional[str] = None):
    """Speak the given text with an optional style."""
    style_str = f" ({style})" if style else ""
    io_adapter.write_output(f"\n[AI{style_str}]: {text}")
    return "Speaking completed"

async def change_emotion(emotion: str):
    """Change the visual emotion."""
    io_adapter.write_output(f"\n[Expression]: {emotion}")
    return "Emotion changed"

async def switch_scene(scene: str):
    """Switch the OBS scene."""
    io_adapter.write_output(f"\n[Scene]: {scene}")
    return "Scene switched"

async def get_comments():
    """Get comments from the adapter."""
    inputs = io_adapter.get_inputs()
    if not inputs:
        return "No new comments."
    return "\n".join(inputs)

# 修正箇所: 未定義の show_headline, show_image を削除しました
TOOLS = {
    "speak": speak,
    "change_emotion": change_emotion,
    "switch_scene": switch_scene,
    "get_comments": get_comments,
}

TOOL_DEFINITIONS = [
    {
        "name": "speak",
        "description": "Speak text to the audience.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "style": {"type": "string"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "change_emotion",
        "description": "Change the avatar's facial expression.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "emotion": {"type": "string"}
            },
            "required": ["emotion"]
        }
    },
    {
        "name": "switch_scene",
        "description": "Switch the displayed scene.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scene": {"type": "string"}
            },
            "required": ["scene"]
        }
    },
    {
        "name": "get_comments",
        "description": "Retrieve user comments.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        }
    }
]

@app.get("/health")
async def health():
    return {"status": "ok"}

# --- MCP Protocol Endpoints ---

@app.get("/sse")
async def handle_sse(request: Request):
    """Handle SSE connections (MCP initialization)."""
    async def event_generator():
        yield {
            "event": "endpoint",
            "data": "/messages"
        }
        while True:
            await asyncio.sleep(1)
            
    return EventSourceResponse(event_generator())

@app.post("/messages")
async def handle_messages(request: Request):
    """Handle JSON-RPC messages (e.g. Call Tool)."""
    try:
        data = await request.json()
    except:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
        
    method = data.get("method")
    msg_id = data.get("id")
    params = data.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": TOOL_DEFINITIONS
            },
            "id": msg_id
        }
    
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name in TOOLS:
            try:
                result = await TOOLS[tool_name](**args)
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": str(result)}]
                    },
                    "id": msg_id
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": str(e)},
                    "id": msg_id
                }
        else:
             return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": "Method not found"},
                "id": msg_id
            }

    if method == "initialize":
         return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "cli-body",
                    "version": "0.1.0"
                }
            },
            "id": msg_id
        }

    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": msg_id}
