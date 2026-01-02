import asyncio
import sys
import threading
from typing import List, Optional

from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

# --- Tools Implementation ---

async def show_headline(text: str):
    """Display a news headline."""
    print(f"\n[Headline]: {text}")
    return "Headline displayed"

async def show_image(url: str):
    """Display an image."""
    print(f"\n[Image]: {url}")
    return "Image displayed"

TOOLS = {
    "show_headline": show_headline,
    "show_image": show_image,
}

TOOL_DEFINITIONS = [
    {
        "name": "show_headline",
        "description": "Display a news headline on the screen.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"]
        }
    },
    {
        "name": "show_image",
        "description": "Display an image on the screen.",
        "inputSchema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }
    }
]

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
                    "name": "news-tool",
                    "version": "0.1.0"
                }
            },
            "id": msg_id
        }

    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": msg_id}
