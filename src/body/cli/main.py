import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.routing import Route
from .tools import speak, change_emotion, get_comments, start_input_reader_thread

import logging

# Configure logging to suppress noisy output
logging.basicConfig(level=logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

mcp = FastMCP("body-cli")

@mcp.tool(name="speak")
async def speak_tool(text: str, style: str = None) -> str:
    """Speak text to the audience."""
    return await speak(text, style)

@mcp.tool(name="change_emotion")
async def change_emotion_tool(emotion: str) -> str:
    """Change the avatar's facial expression."""
    return await change_emotion(emotion)

@mcp.tool(name="sys_get_comments")
async def sys_get_comments() -> str:
    """Retrieve user comments. INTERNAL USE ONLY."""
    return await get_comments()

# Disable DNS rebinding protection for Docker networking
mcp.settings.transport_security.enable_dns_rebinding_protection = False

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok"})

# Get the Starlette app from FastMCP
app = mcp.sse_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    start_input_reader_thread()
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
