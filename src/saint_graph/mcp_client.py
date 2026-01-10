import asyncio
import json
import httpx
import logging
from typing import Dict, Any, List, Union
from google.genai import types

logger = logging.getLogger(__name__)

def convert_schema(schema: Dict[str, Any]) -> types.Schema:
    """
    Recursively converts a JSON Schema dictionary to a Google GenAI types.Schema.
    Simplified implementation for common cases.
    """
    if not schema:
        return None

    type_str = schema.get("type", "OBJECT").upper()
    description = schema.get("description")

    # Handle properties for Objects
    properties = {}
    if "properties" in schema:
        for key, prop_schema in schema["properties"].items():
            properties[key] = convert_schema(prop_schema)

    # Handle items for Arrays
    items = None
    if "items" in schema:
        items = convert_schema(schema["items"])

    # Handle enum
    enum_values = schema.get("enum")

    # Handle required fields
    required = schema.get("required", [])

    return types.Schema(
        type=getattr(types.Type, type_str, types.Type.OBJECT),
        description=description,
        properties=properties if properties else None,
        items=items,
        enum=enum_values,
        required=required if required else None
    )

def convert_mcp_tool_to_genai(mcp_tool: Dict[str, Any]) -> types.FunctionDeclaration:
    """
    Converts a single MCP tool definition to a Gemini FunctionDeclaration.
    """
    return types.FunctionDeclaration(
        name=mcp_tool["name"],
        description=mcp_tool.get("description", ""),
        parameters=convert_schema(mcp_tool.get("inputSchema", {}))
    )

class SingleMCPClient:
    """Internal client for a single MCP server."""
    def __init__(self, base_url: str, http_client: httpx.AsyncClient):
        self.base_url = base_url
        self.post_url = None
        self.tools = []
        self.session_id = 0
        self.http_client = http_client

    async def connect(self):
        logger.info(f"Connecting to MCP at {self.base_url}...")
        try:
            # SSE Handshake (Simplified)
            async with self.http_client.stream("GET", self.base_url) as response:
                 async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        break
        except Exception as e:
            logger.warning(f"Failed to SSE handshake with {self.base_url}: {e}")

        self.post_url = self.base_url.replace("/sse", "/messages")
        await self.initialize()

    async def _send_rpc(self, method: str, params: dict = None):
        self.session_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.session_id
        }
        resp = await self.http_client.post(self.post_url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def initialize(self):
        res = await self._send_rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "saint-graph", "version": "0.1.0"}
        })
        await self.list_tools()

    async def list_tools(self) -> List[Dict[str, Any]]:
        res = await self._send_rpc("tools/list")
        if "result" in res and "tools" in res["result"]:
            self.tools = res["result"]["tools"]
            logger.info(f"Discovered {len(self.tools)} tools on {self.base_url}")
            return self.tools
        self.tools = []
        return []

    async def call_tool(self, name: str, arguments: dict):
        if name != "get_comments":
            logger.info(f"Calling tool: {name} on {self.base_url} with {arguments}")
        res = await self._send_rpc("tools/call", {
            "name": name,
            "arguments": arguments
        })
        if "error" in res:
            raise Exception(f"Tool Error from {self.base_url}: {res['error']}")
        
        if "result" in res and "content" in res["result"] and len(res["result"]["content"]) > 0:
            return res["result"]["content"][0]["text"]
        return ""

class MCPClient:
    """Aggregates multiple MCP servers."""
    def __init__(self, base_urls: Union[str, List[str]]):
        if isinstance(base_urls, str):
            self.urls = [base_urls] if base_urls else []
        else:
            self.urls = base_urls
        
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.clients: List[SingleMCPClient] = []
        self.tool_map: Dict[str, SingleMCPClient] = {} # Tool Name -> Client

    async def connect(self):
        self.clients = [SingleMCPClient(url, self.http_client) for url in self.urls]
        await asyncio.gather(*[c.connect() for c in self.clients])
        
        # Build Tool Map
        self.tool_map = {}
        for c in self.clients:
            for t in c.tools:
                self.tool_map[t['name']] = c
        logger.info(f"Connected to {len(self.clients)} MCP servers. Tools map: {list(self.tool_map.keys())}")

    async def initialize(self):
        # Already handled in connect
        pass

    async def list_tools(self) -> List[Dict[str, Any]]:
        all_tools = []
        for c in self.clients:
            all_tools.extend(c.tools)
        return all_tools

    async def call_tool(self, name: str, arguments: dict):
        client = self.tool_map.get(name)
        if not client:
            raise Exception(f"Tool {name} not found in any MCP server.")
        return await client.call_tool(name, arguments)

    def get_google_genai_tools(self) -> list[types.Tool]:
        tools = []
        for c in self.clients:
             tools.extend(c.tools)
        if not tools:
            return []
        
        genai_funcs = [convert_mcp_tool_to_genai(t) for t in tools]
        return [types.Tool(function_declarations=genai_funcs)]
