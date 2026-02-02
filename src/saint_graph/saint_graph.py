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
        
        音声は並列生成し、再生は順次実行します。
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

            # センテンス単位でパース
            if full_text:
                sentences = self._parse_response(full_text)
                logger.info(f"Parsed {len(sentences)} sentences from AI response")
                
                # 全音声を並列に生成
                async def generate_one(emotion: str, text: str) -> tuple[str, str, str, float]:
                    """1つの音声を生成"""
                    try:
                        # voice.generate_and_save を直接呼び出す（REST経由ではなく）
                        from .body_client import httpx
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.post(
                                f"{self.body.base_url}/api/speak",
                                json={"text": text, "style": emotion},
                                timeout=30.0
                            )
                            # speakは実際には生成だけして返すように変更が必要
                            # 今は既存のspeakを使うため、file_pathとdurationを別途取得するロジックが必要
                            # 簡易実装: speakは生成+再生するので、ここでは順次実行する
                            return (emotion, text, "", 0.0)
                    except Exception as e:
                        logger.error(f"Error generating audio: {e}")
                        return (emotion, text, "", 0.0)
                
                # シンプルな実装: 順次生成+再生（並列生成は次フェーズで実装）
                current_emotion = None
                for emotion, text in sentences:
                    # 感情が変わった場合のみ変更
                    if emotion != current_emotion:
                        await self.body.change_emotion(emotion)
                        current_emotion = emotion
                    
                    # 発話（生成+再生+完了待機）
                    await self.body.speak(text, style=emotion)
                
                logger.info(f"Turn completed. {len(sentences)} sentences spoken")
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

    def _parse_response(self, full_text: str) -> list[tuple[str, str]]:
        """
        テキストから感情タグと文章を抽出し、(emotion, sentence)のリストを返します。
        
        サポート形式:
        - [emotion: happy] 文章1。文章2。
        - [emotion: happy] 文章1。[emotion: sad] 文章2。
        
        Returns:
            [(emotion, sentence), ...] のリスト
        """
        result = []
        current_emotion = "neutral"  # デフォルト感情
        
        # 感情タグとテキストを分割
        parts = re.split(r'(\[emotion:\s*\w+\])', full_text)
        
        current_text = ""
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # 感情タグの場合
            emotion_match = re.match(r'\[emotion:\s*(\w+)\]', part)
            if emotion_match:
                # 前のテキストがあれば保存
                if current_text:
                    sentences = self._split_sentences(current_text)
                    for sent in sentences:
                        if sent.strip():
                            result.append((current_emotion, sent.strip()))
                    current_text = ""
                # 感情を更新
                current_emotion = emotion_match.group(1).lower()
            else:
                # 通常のテキスト
                current_text += part
        
        # 残りのテキストを処理
        if current_text:
            sentences = self._split_sentences(current_text)
            for sent in sentences:
                if sent.strip():
                    result.append((current_emotion, sent.strip()))
        
        # 結果が空の場合はデフォルトを返す
        if not result:
            result = [("neutral", full_text.strip())]
        
        return result
    
    def _split_sentences(self, text: str) -> list[str]:
        """
        テキストを文単位で分割します。
        日本語（。！？）と英語（.!?）の両方に対応。
        """
        # 文末記号で分割
        sentences = re.split(r'([。！？.!?]+)', text)
        
        # 分割結果を再結合（区切り文字を含める）
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]  # 区切り文字を追加
            if sentence.strip():
                result.append(sentence)
        
        # 最後の要素が区切り文字でない場合
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1])
        
        return result if result else [text]

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
