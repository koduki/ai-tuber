from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import uvicorn
from .tools import get_weather

app = FastAPI()

# --- MCP Tool Registry ---
TOOLS = {
    "get_weather": get_weather,
}

TOOL_DEFINITIONS = [
    {
        "name": "get_weather",
        "description": "Retrieve weather information for a specified location and date.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name (e.g. Tokyo, Fukuoka)"},
                "date": {"type": "string", "description": "Date (YYYY-MM-DD) or relative (today, tomorrow). Default is current."}
            },
            "required": ["location"]
        }
    }
]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/sse")
async def handle_sse(request: Request):
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
    try:
        data = await request.json()
    except:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
        
    method = data.get("method")
    msg_id = data.get("id")
    params = data.get("params", {})

    if method == "tools/list":
        return {"jsonrpc": "2.0", "result": {"tools": TOOL_DEFINITIONS}, "id": msg_id}
    
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name in TOOLS:
            try:
                result = await TOOLS[tool_name](**args)
                return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": str(result)}]}, "id": msg_id}
            except Exception as e:
                return {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": msg_id}
        else:
             return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": msg_id}

    if method == "initialize":
         return {"jsonrpc": "2.0", "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "body-weather", "version": "0.1.0"}}, "id": msg_id}

    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": msg_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, access_log=False)
