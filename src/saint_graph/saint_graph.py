import asyncio
import logging
import re
import traceback
from typing import List, Optional, Any, Iterable

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models import Gemini
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_toolset import SseConnectionParams
from google.adk.events.event import Event

from google.genai import types
from .config import logger, MODEL_NAME
from .body_client import BodyClient


def _iter_exception_group(e: BaseException) -> Iterable[BaseException]:
    # Python 3.11 ExceptionGroup / BaseExceptionGroup 対応
    if hasattr(e, "exceptions"):
        for sub in getattr(e, "exceptions", []) or []:
            yield sub
            yield from _iter_exception_group(sub)


class SaintGraph:
    """
    Google ADKを使用してエージェントの振る舞いを管理するコアクラス。
    Body機能はAIのレスポンス（テキスト＋感情タグ）をパースしてREST APIを実行します。
    外部ツール（天気など）は MCP で管理されます。
    """

    def __init__(self, body: BodyClient, mcp_url: str, system_instruction: str, mind_config: Optional[dict] = None, tools: List[Any] = None, templates: Optional[dict[str, str]] = None):
        """
        SaintGraphを初期化します。
        
        Args:
            body: BodyClient インスタンス
            mcp_url: MCPツール用のURL（天気APIなど）
            system_instruction: システム指示文
            mind_config: キャラクター設定辞書 (speaker_id など)
            tools: 追加のカスタムツール（モック等）
            templates: 配信フェーズごとのテンプレート辞書
        """
        self.body = body
        self.system_instruction = system_instruction
        self.mind_config = mind_config or {}
        self.templates = templates or {}
        self.speaker_id = self.mind_config.get("speaker_id")

        # MCP ツールセットの初期化（天気などの外部ツール用）
        self.toolsets = []
        if mcp_url:
            connection_params = SseConnectionParams(url=mcp_url)
            toolset = McpToolset(connection_params=connection_params)
            self.toolsets.append(toolset)
        
        # ツールの統合
        all_tools = self.toolsets + (tools if tools else [])

        self.agent = Agent(
            name="SaintGraph",
            model=Gemini(model=MODEL_NAME),
            instruction=self.system_instruction,
            tools=all_tools if all_tools else None
        )
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"SaintGraph initialized with model {MODEL_NAME}, mcp_url={mcp_url}")

    async def close(self):
        """ツールセットの接続を解除してクリーンアップします。"""
        for ts in self.agent.tools:
            if isinstance(ts, McpToolset) and hasattr(ts, 'close'):
                await ts.close()

    async def process_intro(self):
        """開始挨拶を実行します。"""
        template = self.templates.get("intro", "こんにちは。配信を始めます。")
        await self.process_turn(template, context="Intro")

    async def process_news_reading(self, title: str, content: str):
        """ニュース読み上げを実行します。"""
        template = self.templates.get("news_reading", "ニュース「{title}」を読み上げます。\n{content}")
        instruction = template.format(title=title, content=content)
        await self.process_turn(instruction, context=f"News Reading: {title}")

    async def process_news_finished(self):
        """ニュース全消化時の反応を実行します。"""
        template = self.templates.get("news_finished", "全てのニュースを読み上げました。")
        await self.process_turn(template, context="News Finished")

    async def process_closing(self):
        """締めの挨拶を実行します。"""
        template = self.templates.get("closing", "それでは、本日の配信を終了します。ありがとうございました。")
        await self.process_turn(template, context="Closing")

    # --- メインターン処理 ---

    async def process_turn(self, user_input: str, context: Optional[str] = None):
        """
        単一のインタラクションターンを処理します。
        AIからのテキスト出力を取得し、感情タグ [emotion: ...] をパースして Body API を実行します。
        """
        logger.info(f"Turn started. Input: {user_input[:50]}..., Context: {context}")
        try:
            # セッションの確保
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
                
                current_emotion = None
                for emotion, text in sentences:
                    # 感情が変わった場合のみ変更
                    if emotion != current_emotion:
                        await self.body.change_emotion(emotion)
                        current_emotion = emotion
                    
                    # 発話（完了待機）
                    await self.body.speak(text, style=emotion, speaker_id=self.speaker_id)
                
                logger.info(f"Turn completed. {len(sentences)} sentences spoken")
            else:
                logger.warning("No text output received from AI.")

        except Exception as e:
            logger.error("process_turn failed: %r (%s)", e, type(e))
            logger.error("process_turn traceback:\n%s", traceback.format_exc())
            for i, sub in enumerate(_iter_exception_group(e)):
                logger.error("ExceptionGroup sub[%d]: %r (%s)", i, sub, type(sub))
                logger.error("ExceptionGroup sub[%d] traceback:\n%s", i, "".join(traceback.format_exception(sub)))

            logger.exception("Error in process_turn: %s", e)
            raise

    def _extract_text_from_event(self, event) -> Optional[str]:
        """ADKイベントからテキストを抽出します。"""
        if isinstance(event, Event):
            if hasattr(event, 'content') and event.content:
                parts = getattr(event.content, 'parts', [])
                text_parts = []
                for p in parts:
                    if hasattr(p, 'text') and p.text:
                        text_parts.append(p.text)
                return "".join(text_parts)
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
