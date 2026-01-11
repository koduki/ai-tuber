import asyncio
import logging
from typing import List, Optional, Any

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models import Gemini
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_toolset import SseConnectionParams

from google.genai import types
from .config import logger, MODEL_NAME

class SaintGraph:
    """
    SaintGraph implementation using Google ADK native patterns.
    """
    async def close(self):
        """Cleanup toolset connections."""
        for ts in self.toolsets:
            if hasattr(ts, 'close'):
                await ts.close()

    def __init__(self, mcp_urls: List[str], system_instruction: str, tools: List[Any] = None):
        self.mcp_urls = mcp_urls
        self.system_instruction = system_instruction
        
        # 1. MCP Toolsets initialization
        self.toolsets = tools if tools else []
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
        logger.info(f"Turn started (ADK). Input: {user_input}...")
        try:
            # Ensure session exists
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name, 
                user_id="yt_user", 
                session_id="yt_session"
            )
            if not session:
                await self.runner.session_service.create_session(
                    app_name=self.runner.app_name, 
                    user_id="yt_user", 
                    session_id="yt_session"
                )

            # Iterate over events from run_async
            async for event in self.runner.run_async(
                new_message=types.Content(role="user", parts=[types.Part(text=user_input)]), 
                user_id="yt_user", 
                session_id="yt_session"
            ):
                # Log interesting events if needed
                pass
            
            logger.info(f"Turn completed.")

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
                    
                    extracted_text = None

                    # Helper to get content from object or dict
                    content = getattr(res, 'content', None)
                    if content is None and isinstance(res, dict):
                        content = res.get('content')
                    
                    if content:
                        # Case 1: content is a list (Standard MCP)
                        if isinstance(content, list):
                            texts = []
                            for block in content:
                                if hasattr(block, 'text'):
                                    texts.append(block.text)
                                elif isinstance(block, dict) and 'text' in block:
                                    texts.append(block['text'])
                            if texts:
                                extracted_text = "\n".join(texts)

                        # Case 2: content is a dict with 'result' (Observed in logs)
                        elif isinstance(content, dict) and 'result' in content:
                            extracted_text = content['result']
                    
                    if extracted_text is not None:
                        return extracted_text
                        
                    return str(res)
        raise Exception(f"Tool {name} not found in any toolset.")


