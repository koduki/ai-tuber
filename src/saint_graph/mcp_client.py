import asyncio
import json
import httpx
import logging
from typing import Dict, Any, List
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

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.post_url = None
        self.tools = []
        self.session_id = 0

    async def connect(self):
        """
        Connect to the MCP server via SSE to discover the POST endpoint.
        """
        logger.info(f"Connecting to MCP at {self.base_url}...")
        
        # In a real MCP SSE implementation, we keep the connection open for events.
        # For this MVP body implementation, the server sends the endpoint immediately.
        # We'll just perform a quick read to get the endpoint.
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", self.base_url) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            # Parse the data payload
                            data_str = line[len("data:"):].strip()
                            # For now, we assume this is the endpoint config or we just proceed.
                            # We must break here to avoid hanging forever on the keepalive stream.
                            break
        except Exception as e:
            logger.warning(f"Failed to SSE handshake with {self.base_url}, using fallback: {e}")

        # Fallback/Assumption for endpoint
        self.post_url = self.base_url.replace("/sse", "/messages")
        
        # Now Initialize
        await self.initialize()

    async def _send_rpc(self, method: str, params: dict = None):
        """Send a JSON-RPC 2.0 request."""
        self.session_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.session_id
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.post_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def initialize(self):
        """Perform MCP Handshake."""
        logger.info("Initializing MCP...")
        res = await self._send_rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "saint-graph", "version": "0.1.0"}
        })
        logger.info(f"Initialized: {res}")
        
        # Pre-fetch tools during initialization for backward compatibility/convenience
        await self.list_tools()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        [Standardization] MCPサーバーからツール一覧を取得します。
        公式SDKの session.list_tools() と役割を合わせます。
        """
        res = await self._send_rpc("tools/list")
        if "result" in res and "tools" in res["result"]:
            self.tools = res["result"]["tools"]
            logger.info(f"Discovered {len(self.tools)} tools.")
            return self.tools
        else:
            logger.warning("No tools found.")
            self.tools = []
            return []

    async def call_tool(self, name: str, arguments: dict):
        """
        [Standardization] 指定されたツールを実行します。
        公式SDKの session.call_tool(name, arguments) とインターフェースを合わせます。
        """
        logger.info(f"Calling tool: {name} with {arguments}")
        res = await self._send_rpc("tools/call", {
            "name": name,
            "arguments": arguments
        })
        
        if "error" in res:
            raise Exception(f"Tool Error: {res['error']}")
            
        # Extract content
        # Result -> content -> list of items
        # We usually return just the text for the LLM
        if "result" in res and "content" in res["result"] and len(res["result"]["content"]) > 0:
            return res["result"]["content"][0]["text"]
        return ""

    def get_google_genai_tools(self) -> list[types.Tool]:
        """MCPのツール定義をGemini用の形式に変換して返す"""
        if not self.tools:
            return []
        genai_funcs = [convert_mcp_tool_to_genai(t) for t in self.tools]
        return [types.Tool(function_declarations=genai_funcs)]
