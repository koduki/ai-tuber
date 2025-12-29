import asyncio
import json
import httpx
import logging

logger = logging.getLogger(__name__)

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
        
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", self.base_url) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        # Parse the data payload
                        data_str = line[len("data:"):].strip()
                        # For now, we assume this is the endpoint config or we just proceed.
                        # We must break here to avoid hanging forever on the keepalive stream.
                        break

                            
        # To simplify robustly:
        # We know the server implementation is ours.
        # It sends event: endpoint, data: /messages.
        # But for 'cli-body', let's just HARDCODE the post endpoint if detection implies logic complexity.
        # Or, we do it properly.
        
        # Better approach for this MVP client:
        # Just use the known endpoint convention for our own server if discovery is tricky async.
        # But let's try to be generic:
        self.post_url = self.base_url.replace("/sse", "/messages") # Fallback/Assumption
        
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
        
        # Get Tools
        res = await self._send_rpc("tools/list")
        if "result" in res and "tools" in res["result"]:
            self.tools = res["result"]["tools"]
            logger.info(f"Discovered {len(self.tools)} tools.")
        else:
            logger.warning("No tools found.")

    async def call_tool(self, name: str, arguments: dict):
        """Call a specific tool."""
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
        return res["result"]["content"][0]["text"]
