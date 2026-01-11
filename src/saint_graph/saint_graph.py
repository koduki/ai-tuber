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
        Processes a single turn of interaction with logical control (nudge).
        """
        logger.info(f"Turn started (ADK). Input: {user_input}...")
        try:
            await self._ensure_session()
            
            has_spoken = False
            has_retrieved = False
            found_raw_text = False
            
            def is_tool_call(event, tool_name):
                ev_str = str(event)
                # Heuristic: Check for tool markers in event string representation
                # ADK events for tool calls typically contain name='tool_name'
                if f"name='{tool_name}'" in ev_str or f'name="{tool_name}"' in ev_str:
                    # Ensure it's not just a text description
                    if "TextPart" not in ev_str and "text=" not in ev_str:
                        return True
                return False

            max_attempts = 3
            current_user_message = user_input
            
            for attempt in range(max_attempts):
                found_raw_text = False
                async for event in self.runner.run_async(
                    new_message=types.Content(role="user", parts=[types.Part(text=current_user_message)]), 
                    user_id="yt_user", 
                    session_id="yt_session"
                ):
                    if is_tool_call(event, "speak"):
                        has_spoken = True
                    if is_tool_call(event, "get_weather"):
                        has_retrieved = True
                    
                    # Detect forbidden raw text output
                    ev_str = str(event)
                    if "TextPart" in ev_str and "text=" in ev_str:
                        # Crude check for non-empty text that isn't just whitespace
                        if "text=' '" not in ev_str and 'text=""' not in ev_str:
                            found_raw_text = True
                
                if has_spoken:
                    break
                
                # Nudge Logic: Targeted based on missing state
                if found_raw_text and not (has_spoken or has_retrieved):
                    logger.warning(f"Attempt {attempt + 1}: Unstructured text output detected. Forcing tool usage.")
                    current_user_message = "テキストを直接返してはいけません。必ず speak ツールを使って話してください。情報が必要な場合はツールで検索してください。"
                elif not has_retrieved and ("天気" in user_input or "weather" in user_input.lower()):
                    logger.warning(f"Attempt {attempt + 1}: Retrieval skipped for weather request. Nudging...")
                    current_user_message = "天気を検索してください。勝手に予想せず、必ず get_weather ツールを使用してください。"
                else:
                    logger.warning(f"Attempt {attempt + 1}: Final response (speak) missing. Nudging...")
                    current_user_message = "結果をユーザーに話してください。必ず speak ツールを使用してターンを完了させてください。"

            logger.info(f"Turn completed. Spoken: {has_spoken}, Retrieved: {has_retrieved}")

        except Exception as e:
            logger.error(f"Error in ADK run: {e}", exc_info=True)

    async def _ensure_session(self):
        """Helper to ensure the default session exists."""
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

    async def call_tool(self, name: str, arguments: dict) -> str:
        """
        Utility to call an MCP tool directly (e.g., for polling comments).
        Uses a cache to avoid repeated tool discovery.
        """
        if not hasattr(self, "_tool_cache"):
            self._tool_cache = {}

        # 1. Check cache
        if name in self._tool_cache:
            try:
                res = await self._tool_cache[name].run_async(args=arguments, tool_context=None)
                return self._extract_text(res)
            except Exception as e:
                logger.warning(f"Cached tool {name} call failed, retrying discovery: {e}")
                del self._tool_cache[name]

        # 2. Discover and call
        # Retry discovery a few times if not found (SSE connection might be warming up)
        for attempt in range(5):
            for toolset in self.toolsets:
                try:
                    tools = await toolset.get_tools()
                    for tool in tools:
                        self._tool_cache[tool.name] = tool
                        if tool.name == name:
                            res = await tool.run_async(args=arguments, tool_context=None)
                            return self._extract_text(res)
                except Exception as e:
                    logger.debug(f"Toolset get_tools failed on attempt {attempt}: {e}")
            
            if attempt < 4:
                await asyncio.sleep(1) # Small wait before retry
        
        raise Exception(f"Tool {name} not found in any toolset after retries.")

    def _extract_text(self, res: Any) -> str:
        """Helper to extract text from tool result."""
        extracted_text = None
        # content attribute or dict key
        content = getattr(res, 'content', None)
        if content is None and isinstance(res, dict):
            content = res.get('content')
        
        if content:
            if isinstance(content, list):
                texts = []
                for block in content:
                    if hasattr(block, 'text'):
                        texts.append(block.text)
                    elif isinstance(block, dict) and 'text' in block:
                        texts.append(block['text'])
                if texts:
                    extracted_text = "\n".join(texts)
            elif isinstance(content, dict) and 'result' in content:
                extracted_text = content['result']
        
        if extracted_text is not None:
            return extracted_text
        return str(res)


