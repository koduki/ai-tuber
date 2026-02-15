"""MCP tools for body-streamer service"""
import os
from typing import Optional
import logging
import json
import asyncio
from . import voice, obs, youtube

logger = logging.getLogger(__name__)


async def play_audio_file(file_path: str, duration: float) -> str:
    """
    事前生成された音声ファイルを再生し、完了まで待機します。
    
    Args:
        file_path: WAVファイルのパス
        duration: 再生時間（秒）
        
    Returns:
        実行結果メッセージ
    """
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


async def speak(text: str, style: str = "neutral", speaker_id: Optional[int] = None) -> str:
    """
    視聴者に対してテキストを発話します。
    音声生成と再生を行い、完了まで待機します。
    
    Args:
        text: 発話するテキスト
        style: 発話スタイル (neutral, happy, sad, angry)
        speaker_id: 話者ID (指定された場合はstyleより優先)
        
    Returns:
        実行結果メッセージ
    """
    try:
        # 音声生成
        file_path, duration = await voice.generate_and_save(text, style, speaker_id)
        
        # 音声再生 (完了まで待機)
        result = await play_audio_file(file_path, duration)
        
        logger.info(f"[speak] '{text[:30]}...' (style: {style}, speaker_id: {speaker_id}, {duration:.1f}s)")
        return result
    except Exception as e:
        logger.error(f"Error in speak tool: {e}")
        return f"発話エラー: {str(e)}"


async def change_emotion(emotion: str) -> str:
    """
    アバターの表情（感情）を変更します。
    
    Args:
        emotion: 感情 (neutral, happy, sad, angry)
        
    Returns:
        実行結果メッセージ
    """
    try:
        result = await obs.set_visible_source(emotion)
        logger.info(f"[change_emotion] {emotion}")
        return result
    except Exception as e:
        logger.error(f"Error in change_emotion tool: {e}")
        return f"表情変更エラー: {str(e)}"


async def get_comments() -> str:
    """
    コメントを取得します。
    STREAMING_MODE に応じて、YouTube Live チャットまたは内部キューから取得します。
    
    Returns:
        コメントリスト (JSON形式)
    """
    streaming_mode = os.getenv("STREAMING_MODE", "false").lower() == "true"
    
    try:
        if streaming_mode and _youtube_comment_adapter:
            comments = _youtube_comment_adapter.get()
        else:
            comments = await youtube.get_new_comments()
        
        if not comments:
            return json.dumps([])
        
        logger.info(f"[get_comments] Retrieved {len(comments)} comments")
        return json.dumps(comments, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error in get_comments tool: {e}")
        return json.dumps([])


async def start_obs_recording() -> str:
    """
    OBSの録画を開始します。
    
    Returns:
        実行結果メッセージ
    """
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


async def stop_obs_recording() -> str:
    """
    OBSの録画を停止します。
    
    Returns:
        実行結果メッセージ
    """
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


# Global state for streaming
_youtube_live_adapter = None
_youtube_comment_adapter = None
_current_broadcast_id = None


async def _start_streaming(config: dict) -> str:
    """YouTube Live 配信を開始する内部関数。"""
    global _youtube_live_adapter, _youtube_comment_adapter, _current_broadcast_id
    
    from .youtube_live_adapter import YoutubeLiveAdapter
    
    _youtube_live_adapter = YoutubeLiveAdapter()
    youtube_client, _ = _youtube_live_adapter.authenticate_youtube()
    
    title = config.get("title", "AI Tuber Live Stream")
    description = config.get("description", "")
    scheduled_start_time = config.get("scheduled_start_time", "")
    thumbnail_path = config.get("thumbnail_path")
    privacy_status = config.get("privacy_status", "private")
    
    logger.info(f"Creating YouTube Live broadcast: {title}")
    live_response = _youtube_live_adapter.create_live(
        youtube_client, title, description, scheduled_start_time,
        thumbnail_path, privacy_status
    )
    
    stream_key = live_response['stream']['cdn']['ingestionInfo']['streamName']
    _current_broadcast_id = live_response['broadcast']['id']
    
    logger.info("Starting OBS streaming with YouTube stream key")
    success = await obs.start_streaming(stream_key)
    
    if not success:
        return "OBSストリーミングの開始に失敗しました。"
    
    from .youtube_comment_adapter import YouTubeCommentAdapter
    _youtube_comment_adapter = YouTubeCommentAdapter(_current_broadcast_id)
    
    logger.info(f"[start_streaming] Success - Broadcast ID: {_current_broadcast_id}")
    return f"YouTube Live配信を開始しました。ブロードキャストID: {_current_broadcast_id}"


async def _stop_streaming() -> str:
    """YouTube Live 配信を停止する内部関数。"""
    global _youtube_live_adapter, _youtube_comment_adapter, _current_broadcast_id
    
    logger.info("Stopping OBS streaming")
    await obs.stop_streaming()
    
    if _youtube_live_adapter and _current_broadcast_id:
        youtube_client, _ = _youtube_live_adapter.authenticate_youtube()
        _youtube_live_adapter.stop_live(youtube_client, _current_broadcast_id)
        logger.info(f"Stopped YouTube broadcast: {_current_broadcast_id}")
    
    if _youtube_comment_adapter:
        _youtube_comment_adapter.close()
        _youtube_comment_adapter = None
    
    _current_broadcast_id = None
    
    logger.info("[stop_streaming] Success")
    return "YouTube Live配信を停止しました。"


async def start_broadcast(config: Optional[dict] = None) -> str:
    """
    配信または録画を開始します。
    STREAMING_MODE 環境変数に基づいて自動判定します。
    
    Args:
        config: 配信設定 (title, description, scheduled_start_time, privacy_status 等)
    
    Returns:
        実行結果メッセージ
    """
    streaming_mode = os.getenv("STREAMING_MODE", "false").lower() == "true"
    config = config or {}
    
    try:
        if streaming_mode:
            return await _start_streaming(config)
        else:
            result = await start_obs_recording()
            # OBS録画開始後の安定化待機
            await asyncio.sleep(3)
            return result
    except Exception as e:
        logger.error(f"Error in start_broadcast: {e}")
        return f"配信開始エラー: {str(e)}"


async def stop_broadcast() -> str:
    """
    配信または録画を停止します。
    STREAMING_MODE 環境変数に基づいて自動判定します。
    
    Returns:
        実行結果メッセージ
    """
    streaming_mode = os.getenv("STREAMING_MODE", "false").lower() == "true"
    
    try:
        if streaming_mode:
            return await _stop_streaming()
        else:
            return await stop_obs_recording()
    except Exception as e:
        logger.error(f"Error in stop_broadcast: {e}")
        return f"配信停止エラー: {str(e)}"

