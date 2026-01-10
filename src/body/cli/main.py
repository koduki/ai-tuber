import asyncio
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

# Import separated business logic layer
from .tools import speak, change_emotion, get_comments

app = FastAPI()

# --- Tool Registry ---
TOOLS = {
    "speak": speak,
    "change_emotion": change_emotion,
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
