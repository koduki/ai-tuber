import asyncio
import logging
import re
from typing import List, Optional, Any

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models import Gemini
from google.adk.tools import McpToolset, FunctionTool
from google.adk.tools.mcp_tool.mcp_toolset import SseConnectionParams

from google.genai import types
from .config import logger, MODEL_NAME
from .body_client import BodyClient


class SaintGraph:
    """
    Google ADKを使用してエージェントの振る舞いを管理するコアクラス。
    Body機能はAIのレスポンス（テキスト＋感情タグ）をパースしてREST APIを実行します。
    外部ツール（天気など）や明示的な制御（録画など）はMCPまたはローカルツールで呼び出されます。
    """

    def __init__(self, body_url: str, mcp_urls: List[str], system_instruction: str, tools: List[Any] = None):
        """
        SaintGraphを初期化します。
        
        Args:
            body_url: Body REST APIのベースURL (例: http://body-cli:8000)
            mcp_urls: MCPツール用のURL（天気APIなど）
            system_instruction: システム指示文
            tools: 追加のカスタムツール（モック等）
        """
        self.system_instruction = system_instruction
        
        # Body REST APIクライアントの初期化
        self.body = BodyClient(base_url=body_url)
        
        # MCP ツールセットの初期化（天気などの外部ツール用）
        self.toolsets = []
        for url in mcp_urls:
            connection_params = SseConnectionParams(url=url)
            toolset = McpToolset(connection_params=connection_params)
            self.toolsets.append(toolset)
        
        # 明示的な制御ツール（AIが自発的に呼べるもの）
        self.local_tools = [
            FunctionTool(self.start_recording),
            FunctionTool(self.stop_recording)
        ]
        
        # エージェントの構成
        # speak/change_emotion はツールとして登録せず、レスポンスパースで対応
        all_tools = self.local_tools + self.toolsets + (tools if tools else [])
        self.agent = Agent(
            name="SaintV2",
            model=Gemini(model=MODEL_NAME),
            instruction=system_instruction,
            tools=all_tools if all_tools else None
        )
        
        # ランナーの初期化
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"SaintGraph initialized with model {MODEL_NAME}, body_url={body_url}")

    async def close(self):
        """ツールセットの接続を解除してクリーンアップします。"""
        for ts in self.toolsets:
            if hasattr(ts, 'close'):
                await ts.close()

    # --- 録画制御ツール (AIが呼べる) ---

    async def start_recording(self) -> str:
        """OBSの録画を開始します。"""
        return await self.body.start_recording()

    async def stop_recording(self) -> str:
        """OBSの録画を停止します。"""
        return await self.body.stop_recording()

    # --- メインターン処理 ---

    async def process_turn(self, user_input: str, context: Optional[str] = None):
        """
        単一のインタラクションターンを処理します。
        AIからのテキスト出力を取得し、感情タグ [emotion: ...] をパースして Body API を実行します。
        """
        logger.info(f"Turn started. Input: {user_input[:50]}..., Context: {context}")
        try:
            await self._ensure_session()
            
            current_user_message = user_input
            if context:
                current_user_message = f"[{context}]\n{user_input}"
            
            # AIからの全テキストを蓄積
            full_text = ""
            
            async for event in self.runner.run_async(
                new_message=types.Content(role="user", parts=[types.Part(text=current_user_message)]), 
                user_id="yt_user", 
                session_id="yt_session"
            ):
                # テキストパートを抽出
                t = self._extract_text_from_event(event)
                if t:
                    full_text += t

            # 感情タグと本文パース
            if full_text:
                emotion, text = self._parse_response(full_text)
                
                # 感情変更の実行
                await self.body.change_emotion(emotion)
                
                # 発話の実行
                await self.body.speak(text)
                
                logger.info(f"Turn completed. Emotion: {emotion}, Text: {text[:30]}...")
            else:
                logger.warning("No text output received from AI.")

        except Exception as e:
            logger.error(f"Error in process_turn: {e}", exc_info=True)

    def _extract_text_from_event(self, event) -> Optional[str]:
        """ADKイベントからテキストを抽出します。"""
        try:
            from google.adk.events.event import Event
            if isinstance(event, Event):
                if hasattr(event, 'content') and event.content:
                    parts = getattr(event.content, 'parts', [])
                    text_parts = []
                    for p in parts:
                        if hasattr(p, 'text') and p.text:
                            text_parts.append(p.text)
                    return "".join(text_parts)
        except:
            pass
        return None

    def _parse_response(self, full_text: str) -> (str, str):
        """
        テキストから感情タグ [emotion: ...] を抽出し、本文と分離します。
        """
        # [emotion: type] を探す
        match = re.search(r'\[emotion:\s*(\w+)\]', full_text)
        if match:
            emotion = match.group(1).lower()
            # タグを除去した残りを本文とする
            # 全てのタグを置換
            clean_text = re.sub(r'\[emotion:\s*\w+\]', '', full_text).strip()
            return emotion, clean_text
        else:
            # タグが見つからない場合はデフォルトで neutral
            return "neutral", full_text.strip()

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

    async def call_tool(self, name: str, arguments: dict) -> str:
        """
        ツールを直接呼び出します（コメント用など）。
        """
        # ローカルツール
        if name == "start_recording":
            return await self.start_recording()
        if name == "stop_recording":
            return await self.stop_recording()

        # MCPツール
        for toolset in self.toolsets:
            tools = await toolset.get_tools()
            for tool in tools:
                if tool.name == name:
                    res = await tool.run_async(args=arguments, tool_context=None)
                    return self._extract_mcp_text(res)
        
        raise Exception(f"Tool {name} not found.")

    def _extract_mcp_text(self, res: Any) -> str:
        """ツール実行結果からテキストを抽出"""
        if hasattr(res, 'content') and res.content:
            if isinstance(res.content, list) and len(res.content) > 0:
                return getattr(res.content[0], 'text', str(res))
        return str(res)
