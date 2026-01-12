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
    Google ADKを使用してエージェントの振る舞いを管理するコアクラス。
    """

    def __init__(self, mcp_urls: List[str], system_instruction: str, retry_templates: dict = None, tools: List[Any] = None):
        """
        SaintGraphを初期化します。MCPツールセットとADKエージェントのセットアップを行います。
        """
        self.mcp_urls = mcp_urls
        self.system_instruction = system_instruction
        self.retry_templates = retry_templates or {}
        
        # MCP ツールセットの初期化
        self.toolsets = tools if tools else []
        for url in mcp_urls:
            connection_params = SseConnectionParams(url=url)
            toolset = McpToolset(connection_params=connection_params)
            self.toolsets.append(toolset)
        
        # エージェントの構成
        self.agent = Agent(
            name="SaintV2",
            model=Gemini(model=MODEL_NAME),
            instruction=system_instruction,
            tools=self.toolsets
        )
        
        # ランナーの初期化
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"SaintGraph (ADK Native) initialized with model {MODEL_NAME}")

    async def close(self):
        """ツールセットの接続を解除してクリーンアップします。"""
        for ts in self.toolsets:
            if hasattr(ts, 'close'):
                await ts.close()

    # --- イベント解析ヘルパー ---

    def _is_tool_call(self, event, tool_name: str) -> bool:
        """
        イベントが特定のツール呼び出しを表しているか判定します。
        """
        try:
            from google.adk.events.event import Event
            if isinstance(event, Event):
                if hasattr(event, 'content') and event.content is not None:
                    parts = getattr(event.content, 'parts', None)
                    if parts is not None:
                        for part in parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                if part.function_call.name == tool_name:
                                    return True
        except (ImportError, AttributeError):
            pass
        
        # フォールバック：文字列ベースの判定
        ev_str = str(event)
        if f"name='{tool_name}'" in ev_str or f'name="{tool_name}"' in ev_str:
            if "TextPart" not in ev_str and "text=" not in ev_str:
                return True
        return False

    def _detect_raw_text(self, event) -> bool:
        """
        イベントがツールを経由しない生テキスト出力を含むかを判定します。
        """
        ev_str = str(event)
        if "TextPart" in ev_str and "text=" in ev_str:
            if "text=' '" not in ev_str and 'text=""' not in ev_str:
                return True
        return False

    # --- メインターン処理 ---

    async def process_turn(self, user_input: str, context: Optional[str] = None):
        """
        単一のインタラクションターンを処理します。ツール使用の強制（再指示）ロジックを含みます。
        """
        logger.info(f"Turn started (ADK). Input: {user_input[:50]}..., Context: {context}")
        try:
            await self._ensure_session()
            
            has_spoken = False
            has_retrieved = False
            found_raw_text = False

            max_attempts = 3
            current_user_message = user_input
            if context:
                current_user_message = f"[{context}]\n{user_input}"
            
            # 最大3回のトライで望ましい回答（speakツールの使用）を誘導
            for attempt in range(max_attempts):
                found_raw_text = False
                async for event in self.runner.run_async(
                    new_message=types.Content(role="user", parts=[types.Part(text=current_user_message)]), 
                    user_id="yt_user", 
                    session_id="yt_session"
                ):
                    if self._is_tool_call(event, "speak"):
                        has_spoken = True
                    if self._is_tool_call(event, "get_weather"):
                        has_retrieved = True
                    if self._detect_raw_text(event):
                        found_raw_text = True
                
                if has_spoken:
                    break
                
                # 再指示（Retry）ロジック：ツール使用状況に基づき誘導
                if found_raw_text and not has_retrieved:
                    logger.warning(f"Attempt {attempt + 1}: Unstructured text output detected. Retrying...")
                    current_user_message = self.retry_templates.get("retry_no_tool", "テキストを直接返さず、必ず speak ツールを使って話してください。")
                else:
                    logger.warning(f"Attempt {attempt + 1}: turn incomplete (speak tool missing). Retrying...")
                    current_user_message = self.retry_templates.get("retry_final_response", "最後に speak ツールを使用してターンを完了させてください。")

            logger.info(f"Turn completed. Spoken: {has_spoken}, Retrieved: {has_retrieved}")

        except Exception as e:
            logger.error(f"Error in ADK run: {e}", exc_info=True)

    # --- セッション管理 ---

    async def _ensure_session(self):
        """セッションが存在することを確認し、なければ作成します。"""
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

    # --- ツール呼び出しユーティリティ ---

    async def call_tool(self, name: str, arguments: dict) -> str:
        """
        MCPツールを直接呼び出します（コメントのポーリングなどに使用）。
        内部的にツールオブジェクトをキャッシュして再利用します。
        """
        if not hasattr(self, "_tool_cache"):
            self._tool_cache = {}

        # キャッシュの確認
        if name in self._tool_cache:
            try:
                res = await self._tool_cache[name].run_async(args=arguments, tool_context=None)
                return self._extract_text(res)
            except Exception as e:
                logger.warning(f"Cached tool {name} call failed, retrying discovery: {e}")
                del self._tool_cache[name]

        # ツールの探索と実行
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
                await asyncio.sleep(1)
        
        raise Exception(f"Tool {name} not found in any toolset after retries.")

    def _extract_text(self, res: Any) -> str:
        """ツール実行結果からテキストコンテンツを抽出します。"""
        extracted_text = None
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
