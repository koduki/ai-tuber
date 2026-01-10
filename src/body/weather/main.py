import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.routing import Route
from .tools import get_weather

import logging

# Configure logging to suppress noisy output
logging.basicConfig(level=logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

mcp = FastMCP("body-weather")

@mcp.tool(name="get_weather")
async def weather_tool(location: str, date: str = None) -> str:
    """
    Retrieve weather information for a specified location and date.
    location: City name (e.g. Tokyo, Fukuoka)
    date: Date (YYYY-MM-DD) or relative (today, tomorrow). Default is current.
    """
    return await get_weather(location, date)

# Disable DNS rebinding protection for Docker networking
mcp.settings.transport_security.enable_dns_rebinding_protection = False

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok"})

# Get the Starlette app from FastMCP
app = mcp.sse_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
