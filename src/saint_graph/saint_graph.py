import asyncio
import logging
from typing import List, Optional

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models import Gemini
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_toolset import SseConnectionParams

from .config import logger, MODEL_NAME

class SaintGraph:
    """
    SaintGraph implementation using Google ADK native patterns.
    """
    def __init__(self, mcp_urls: List[str], system_instruction: str):
        self.mcp_urls = mcp_urls
        self.system_instruction = system_instruction
        
        # 1. MCP Toolsets initialization
        self.toolsets = []
        for url in mcp_urls:
            # We use SseConnectionParams for ADK's McpToolset
            connection_params = SseConnectionParams(url=url)
            toolset = McpToolset(connection_params=connection_params)
            self.toolsets.append(toolset)
        
        # 2. Agent configuration
        # ADK's Agent handles tool conversion and model interaction
        self.agent = Agent(
            name="SaintV2",
            model=Gemini(model=MODEL_NAME),
            instruction=system_instruction,
            tools=self.toolsets
        )
        
        # 3. Runner initialization
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"SaintGraph (ADK Native) initialized with model {MODEL_NAME}")

    async def process_turn(self, user_input: str):
        """
        Processes a single turn of interaction using ADK's Runner.
        This handles the inner loop (multi-turn tool calls) automatically.
        """
        logger.info(f"Turn started (ADK). Input: {user_input[:30]}...")
        try:
            # run_debug is a high-level helper that manages the session and yields events.
            # verbose=True will print tool calls and responses to the console.
            await self.runner.run_debug(
                user_input, 
                user_id="yt_user", 
                session_id="yt_session", 
                verbose=True
            )
        except Exception as e:
            logger.error(f"Error in ADK run: {e}", exc_info=True)

    async def call_tool(self, name: str, arguments: dict) -> str:
        """
        Utility to call an MCP tool directly (e.g., for polling comments).
        """
        for toolset in self.toolsets:
            tools = await toolset.get_tools()
            for tool in tools:
                if tool.name == name:
                    # In ADK, run_async usually expects a ToolContext.
                    # For direct polling calls where context is not needed, we pass None.
                    res = await tool.run_async(args=arguments, tool_context=None)
                    return str(res)
        raise Exception(f"Tool {name} not found in any toolset.")

    async def close(self):
        """Cleanup toolset connections."""
        for ts in self.toolsets:
            await ts.close()
