import asyncio
import logging
from typing import List, Dict, Any
from google.genai import types

from .mcp_client import MCPClient
from .tools_mapper import convert_mcp_tool_to_genai

logger = logging.getLogger(__name__)

class MultiMCPClient:
    """
    Manages connections to multiple MCP servers and routes tool calls.
    """
    def __init__(self, base_urls: List[str]):
        self.clients = [MCPClient(url) for url in base_urls]
        self.tool_map: Dict[str, MCPClient] = {} # Map tool_name -> client

    async def connect(self):
        """Connect to all MCP servers."""
        logger.info(f"Connecting to {len(self.clients)} MCP servers...")

        # Connect concurrently
        results = await asyncio.gather(*[client.connect() for client in self.clients], return_exceptions=True)

        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Failed to connect to client {self.clients[i].base_url}: {res}")
            else:
                # Register tools from this client
                for tool in self.clients[i].tools:
                    self.tool_map[tool["name"]] = self.clients[i]

        logger.info(f"Total tools available: {len(self.tool_map)}")

    async def call_tool(self, name: str, arguments: dict):
        """Route tool call to the correct client."""
        if name not in self.tool_map:
            raise Exception(f"Tool '{name}' not found in any connected MCP server.")

        client = self.tool_map[name]
        return await client.call_tool(name, arguments)
