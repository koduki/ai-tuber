"""MCP tools for body-streamer service"""
import os
from typing import Optional, Dict, Any
import logging
import json
import asyncio
from . import voice, obs, youtube
from ..service import BodyServiceBase

logger = logging.getLogger(__name__)


class StreamerBodyService(BodyServiceBase):
    """BodyStreamer サービスの実装。"""

    def __init__(self):
        self._youtube_live_adapter = None
        self._youtube_comment_adapter = None
        self._current_broadcast_id = None
        self._action_queue = asyncio.Queue()
        self._worker_task = None

    async def start_worker(self):
        """バックグラウンドワーカーを開始します。"""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._action_worker())
            logger.info("Action worker started")

    async def stop_worker(self):
        """バックグラウンドワーカーを停止します。"""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            logger.info("Action worker stopped")

    async def _action_worker(self):
        """キューからタスクを取り出して順次実行するワーカー。"""
        logger.info("Action worker loop entered")
        while True:
            try:
                task = await self._action_queue.get()
                task_type = task.get("type")
                
                if task_type == "speak":
                    text = task.get("text")
                    style = task.get("style")
                    speaker_id = task.get("speaker_id")
                    
                    # 実際に音声生成と再生を行う
                    try:
                        file_path, duration = await voice.generate_and_save(text, style, speaker_id)
                        await self.play_audio_file(file_path, duration)
                        logger.info(f"[Worker:speak] Completed: {text[:30]}...")
                    except Exception as e:
                        logger.error(f"Error in worker speak task: {e}")
                
                elif task_type == "change_emotion":
                    emotion = task.get("emotion")
                    try:
                        await obs.set_visible_source(emotion)
                        logger.info(f"[Worker:emotion] Changed to {emotion}")
                    except Exception as e:
                        logger.error(f"Error in worker emotion task: {e}")
                
                self._action_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in action worker loop: {e}")
                await asyncio.sleep(1)

    async def speak(self, text: str, style: str = "neutral", speaker_id: Optional[int] = None) -> str:
        """視聴者に対してテキストを発話します (キューに追加して即時復帰)。"""
        await self._action_queue.put({
            "type": "speak",
            "text": text,
            "style": style,
            "speaker_id": speaker_id
        })
        logger.info(f"[speak:queued] '{text[:30]}...'")
        return "Speech queued"

    async def change_emotion(self, emotion: str) -> str:
        """アバターの表情（感情）を変更します (キューに追加して即時復帰)。"""
        await self._action_queue.put({
            "type": "change_emotion",
            "emotion": emotion
        })
        logger.info(f"[change_emotion:queued] {emotion}")
        return "Emotion change queued"

    async def get_comments(self) -> str:
        """コメントを取得します。"""
        streaming_mode = os.getenv("STREAMING_MODE", "false").lower() == "true"
        
        try:
            if streaming_mode and self._youtube_comment_adapter:
                comments = self._youtube_comment_adapter.get()
            else:
                comments = await youtube.get_new_comments()
            
            if not comments:
                return json.dumps([])
            
            logger.info(f"[get_comments] Retrieved {len(comments)} comments")
            return json.dumps(comments, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error in get_comments tool: {e}")
            return json.dumps([])

    async def start_broadcast(self, config: Optional[Dict[str, Any]] = None) -> str:
        """配信または録画を開始します。"""
        streaming_mode = os.getenv("STREAMING_MODE", "false").lower() == "true"
        config = config or {}
        
        try:
            if streaming_mode:
                return await self._start_streaming(config)
            else:
                result = await self.start_obs_recording()
                # OBS録画開始後の安定化待機
                await asyncio.sleep(3)
                return result
        except Exception as e:
            logger.error(f"Error in start_broadcast: {e}")
            return f"配信開始エラー: {str(e)}"

    async def stop_broadcast(self) -> str:
        """配信または録画を停止します。"""
        # すべての発話が完了するまで待機してから停止する
        await self.wait_for_queue()

        streaming_mode = os.getenv("STREAMING_MODE", "false").lower() == "true"
        
        try:
            if streaming_mode:
                return await self._stop_streaming()
            else:
                return await self.stop_obs_recording()
        except Exception as e:
            logger.error(f"Error in stop_broadcast: {e}")
            return f"配信停止エラー: {str(e)}"

    async def wait_for_queue(self) -> str:
        """キューが空になるまで待機します。"""
        logger.info("Waiting for action queue to be empty...")
        await self._action_queue.join()
        logger.info("Action queue is empty")
        return "All queued actions completed"

    # --- ヘルパーメソッドおよび固有メソッド ---

    async def play_audio_file(self, file_path: str, duration: float) -> str:
        """事前生成された音声ファイルを再生し、完了まで待機します。"""
        try:
            await obs.set_source_visibility("voice", True)
            await obs.refresh_media_source("voice", file_path)
            
            # 再生完了まで待機（バッファとして0.2秒追加）
            await asyncio.sleep(duration + 0.2)
            
            logger.info(f"[play_audio_file] Completed playback ({duration:.1f}s)")
            return f"再生完了 ({duration:.1f}s)"
        except Exception as e:
            logger.error(f"Error in play_audio_file: {e}")
            return f"再生エラー: {str(e)}"

    async def start_obs_recording(self) -> str:
        """OBSの録画を開始します。"""
        try:
            success = await obs.start_recording()
            if success:
                logger.info("[start_obs_recording] Success")
                return "OBS録画を開始しました。"
            else:
                logger.warning("[start_obs_recording] Failed")
                return "OBS録画の開始に失敗しました。接続を確認してください。"
        except Exception as e:
            logger.error(f"Error in start_obs_recording tool: {e}")
            return f"録画開始エラー: {str(e)}"

    async def stop_obs_recording(self) -> str:
        """OBSの録画を停止します。"""
        try:
            success = await obs.stop_recording()
            if success:
                logger.info("[stop_obs_recording] Success")
                return "OBS録画を停止しました。"
            else:
                logger.warning("[stop_obs_recording] Failed")
                return "OBS録画の停止に失敗しました。接続を確認してください。"
        except Exception as e:
            logger.error(f"Error in stop_obs_recording tool: {e}")
            return f"録画停止エラー: {str(e)}"

    async def _start_streaming(self, config: dict) -> str:
        """YouTube Live 配信を開始する内部関数。"""
        from .youtube_live_adapter import YoutubeLiveAdapter
        
        self._youtube_live_adapter = YoutubeLiveAdapter()
        youtube_client, _ = self._youtube_live_adapter.authenticate_youtube()
        
        title = config.get("title", "AI Tuber Live Stream")
        description = config.get("description", "")
        scheduled_start_time = config.get("scheduled_start_time", "")
        thumbnail_path = config.get("thumbnail_path")
        privacy_status = config.get("privacy_status", "private")
        
        logger.info(f"Creating YouTube Live broadcast: {title}")
        live_response = self._youtube_live_adapter.create_live(
            youtube_client, title, description, scheduled_start_time,
            thumbnail_path, privacy_status
        )
        
        stream_key = live_response['stream']['cdn']['ingestionInfo']['streamName']
        self._current_broadcast_id = live_response['broadcast']['id']
        
        logger.info("Starting OBS streaming with YouTube stream key")
        success = await obs.start_streaming(stream_key)
        
        if not success:
            return "OBSストリーミングの開始に失敗しました。"
        
        from .youtube_comment_adapter import YouTubeCommentAdapter
        self._youtube_comment_adapter = YouTubeCommentAdapter(self._current_broadcast_id)
        
        logger.info(f"[start_streaming] Success - Broadcast ID: {self._current_broadcast_id}")
        return f"YouTube Live配信を開始しました。ブロードキャストID: {self._current_broadcast_id}"

    async def _stop_streaming(self) -> str:
        """YouTube Live 配信を停止する内部関数。"""
        logger.info("Stopping OBS streaming")
        await obs.stop_streaming()
        
        if self._youtube_live_adapter and self._current_broadcast_id:
            youtube_client, _ = self._youtube_live_adapter.authenticate_youtube()
            self._youtube_live_adapter.stop_live(youtube_client, self._current_broadcast_id)
            logger.info(f"Stopped YouTube broadcast: {self._current_broadcast_id}")
        
        if self._youtube_comment_adapter:
            self._youtube_comment_adapter.close()
            self._youtube_comment_adapter = None
        
        self._current_broadcast_id = None
        
        logger.info("[stop_streaming] Success")
        return "YouTube Live配信を停止しました。"


# Singleton インスタンス
body_service = StreamerBodyService()
