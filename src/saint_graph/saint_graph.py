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

    def __init__(self, body: BodyClient, weather_mcp_url: str, system_instruction: str, mind_config: Optional[dict] = None, tools: List[Any] = None, templates: Optional[dict[str, str]] = None):
        """
        SaintGraphを初期化します。
        
        Args:
            body: BodyClient インスタンス
            weather_mcp_url: MCPツール用のURL（天気APIなど）
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
        if weather_mcp_url:
            connection_params = SseConnectionParams(url=weather_mcp_url)
            toolset = McpToolset(connection_params=connection_params)
            self.toolsets.append(toolset)
        
        # ツールの統合
        all_tools = self.toolsets + (tools if tools else [])

        self.agent = Agent(
            name="SaintGraph",
            model=Gemini(model=MODEL_NAME),
            instruction=self.system_instruction,
            tools=all_tools
        )
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"SaintGraph initialized with model {MODEL_NAME}, weather_mcp_url={weather_mcp_url}")

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
        AIからのテキスト出力を取得し、随時パースして文章単位でストリーミング的に Body API (TTS) を実行します。
        """
        logger.info(f"Turn started. Input: {user_input[:50]}..., Context: {context}")
        max_retries = 3
        for attempt in range(max_retries):
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
                
                buffered_text = ""
                current_emotion = "neutral"
                # ターン開始時に「無言」状態から「通常」状態へリセット
                await self.body.change_emotion(current_emotion)
                sentences_spoken = 0

                # AIからのテキスト出力をストリーミング的に処理
                async for event in self.runner.run_async(
                    new_message=types.Content(role="user", parts=[types.Part(text=current_user_message)]), 
                    user_id="yt_user", 
                    session_id="yt_session"
                ):
                    # テキストパートを抽出
                    t = self._extract_text_from_event(event)
                    if t:
                        buffered_text += t
                        
                        # バッファされたテキストから文や感情タグを随時抽出して処理
                        buffered_text, current_emotion, count = await self._process_buffered_text(
                            buffered_text, current_emotion
                        )
                        sentences_spoken += count

                # 残りのバッファがあれば最後に処理
                if buffered_text.strip():
                    buffered_text, current_emotion, count = await self._process_buffered_text(
                        buffered_text, current_emotion, flush=True
                    )
                    sentences_spoken += count

                if sentences_spoken > 0:
                    # このターンで投げた内容を全て話し終えるまで待機（配信のリズム維持のため）
                    logger.info("Waiting for speech to finish before completing turn...")
                    await self.body.wait_for_queue()
                    
                    # 話し終わったら「無言」状態に切り替える
                    await self.body.change_emotion("silent")
                    
                    logger.info(f"Turn completed. {sentences_spoken} sentences spoken")
                else:
                    logger.warning("No text output received from AI.")
                
                # 成功したらループを抜ける
                return

            except Exception as e:
                # 503 Service Unavailable または Resource Exhausted の場合はリトライ
                error_msg = str(e).upper()
                if ("503" in error_msg or "UNAVAILABLE" in error_msg or "429" in error_msg or "EXHAUSTED" in error_msg) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Transient error in process_turn: {e}. Retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue

                logger.error("process_turn failed: %r (%s)", e, type(e))
                logger.error("process_turn traceback:\n%s", traceback.format_exc())
                for i, sub in enumerate(_iter_exception_group(e)):
                    logger.error("ExceptionGroup sub[%d]: %r (%s)", i, sub, type(sub))
                    logger.error("ExceptionGroup sub[%d] traceback:\n%s", i, "".join(traceback.format_exception(sub)))

                logger.exception("Error in process_turn: %s", e)
                raise
                
    async def _process_buffered_text(self, buffered_text: str, current_emotion: str, flush: bool = False) -> tuple[str, str, int]:
        """
        バッファされた文字列を解析し、完成した文があればTTSキューに送信。
        残りの未完成な文字列と現在の感情を返します。
        """
        count = 0
        while True:
            # 感情タグのチェックと抽出 (先頭から)
            emotion_match = re.search(r'\[emotion:\s*(\w+)\]', buffered_text)
            if emotion_match:
                # タグより前にテキストがあれば、まずはそれを文として処理
                pre_text = buffered_text[:emotion_match.start()]
                if pre_text.strip():
                    sentences = self._split_sentences(pre_text, force_flush=flush)
                    # 最後の要素以外（=完成した文）を送信
                    for i in range(len(sentences) - 1):
                        if sentences[i].strip():
                            await self._speak_sentence(sentences[i].strip(), current_emotion)
                            count += 1
                    
                    if len(sentences) > 0:
                        last_part = sentences[-1]
                        if flush and last_part.strip():
                            await self._speak_sentence(last_part.strip(), current_emotion)
                            count += 1
                            last_part = ""
                        # 残りのテキストはまだ送信せず、感情タグ移行のバッファにする
                        buffered_text = last_part + buffered_text[emotion_match.end():]
                    else:
                        buffered_text = buffered_text[emotion_match.end():]
                else:
                    # 感情の更新
                    new_emotion = emotion_match.group(1).lower()
                    if new_emotion != current_emotion:
                        await self.body.change_emotion(new_emotion)
                        current_emotion = new_emotion
                    buffered_text = buffered_text[emotion_match.end():]
                continue # タグを処理したら再度ループで次のパーツを探す

            # 感情タグがない場合、文の区切りを探す
            sentences = self._split_sentences(buffered_text, force_flush=flush)
            
            # 区切られた文が1つ以下（=まだ文が完了していない）でflushフラグもない場合は待機
            if not flush and len(sentences) <= 1:
                break
                
            # 完成した文を送信
            for i in range(len(sentences) - 1):
                if sentences[i].strip():
                    await self._speak_sentence(sentences[i].strip(), current_emotion)
                    count += 1
            
            # バッファの更新
            if len(sentences) > 0:
                buffered_text = sentences[-1]
                if flush and buffered_text.strip():
                    await self._speak_sentence(buffered_text.strip(), current_emotion)
                    count += 1
                    buffered_text = ""
            else:
                buffered_text = ""
            break
            
        return buffered_text, current_emotion, count

    async def _speak_sentence(self, sentence: str, emotion: str):
        """1文を発話キューに入れます。"""
        # 単純なタグは除去
        sentence = re.sub(r'\[emotion:\s*(\w+)\]', '', sentence).strip()
        if sentence:
            logger.debug(f"Streaming sentence to TTS: {sentence[:30]}... (emotion: {emotion})")
            await self.body.speak(sentence, style=emotion, speaker_id=self.speaker_id)

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

    def _split_sentences(self, text: str, force_flush: bool = False) -> list[str]:
        """
        テキストを区切りません。
        一括でVoiceVoxに渡すことで、OBSでの2.5秒のリップシンクラグによる「文ごとの不自然な間」を解消します。
        """
        return [text]
