"""MCP tools for body-streamer service"""
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
    ユーザーからのコメントを取得します。
    システム内部用ツールとして設計されており、エージェントによる直接呼び出しは想定していません。
    
    Returns:
        コメントリスト (JSON形式)
    """
    try:
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


async def start_streaming(title: str, description: str, scheduled_start_time: str, 
                         thumbnail_path: Optional[str] = None, privacy_status: str = "private") -> str:
    """
    YouTube Live配信を開始します。
    
    Args:
        title: 配信タイトル
        description: 配信説明
        scheduled_start_time: 開始予定時刻 (ISO 8601形式)
        thumbnail_path: サムネイル画像パス (オプション)
        privacy_status: 公開設定 (private, unlisted, public)
        
    Returns:
        実行結果メッセージ
    """
    global _youtube_live_adapter, _youtube_comment_adapter, _current_broadcast_id
    
    try:
        # Import YouTube Live adapter
        from .youtube_live_adapter import YoutubeLiveAdapter
        
        # Create YouTube Live adapter
        _youtube_live_adapter = YoutubeLiveAdapter()
        
        # Authenticate
        youtube_client = _youtube_live_adapter.authenticate_youtube()
        
        # Create live broadcast
        logger.info(f"Creating YouTube Live broadcast: {title}")
        live_response = _youtube_live_adapter.create_live(
            youtube_client, 
            title, 
            description, 
            scheduled_start_time,
            thumbnail_path,
            privacy_status
        )
        
        # Extract stream key and broadcast ID
        stream_key = live_response['stream']['cdn']['ingestionInfo']['streamName']
        _current_broadcast_id = live_response['broadcast']['id']
        
        # Start OBS streaming
        logger.info("Starting OBS streaming with YouTube stream key")
        success = await obs.start_streaming(stream_key)
        
        if not success:
            return "OBSストリーミングの開始に失敗しました。"
        
        # Start comment polling using YouTube Comment Adapter
        from .youtube_comment_adapter import YouTubeCommentAdapter
        _youtube_comment_adapter = YouTubeCommentAdapter(_current_broadcast_id)
        
        logger.info(f"[start_streaming] Success - Broadcast ID: {_current_broadcast_id}")
        return f"YouTube Live配信を開始しました。ブロードキャストID: {_current_broadcast_id}"
        
    except Exception as e:
        logger.error(f"Error in start_streaming tool: {e}")
        return f"配信開始エラー: {str(e)}"


async def stop_streaming() -> str:
    """
    YouTube Live配信を停止します。
    
    Returns:
        実行結果メッセージ
    """
    global _youtube_live_adapter, _youtube_comment_adapter, _current_broadcast_id
    
    try:
        # Stop OBS streaming
        logger.info("Stopping OBS streaming")
        await obs.stop_streaming()
        
        # Stop YouTube broadcast
        if _youtube_live_adapter and _current_broadcast_id:
            youtube_client = _youtube_live_adapter.authenticate_youtube()
            _youtube_live_adapter.stop_live(youtube_client, _current_broadcast_id)
            logger.info(f"Stopped YouTube broadcast: {_current_broadcast_id}")
        
        # Close comment adapter
        if _youtube_comment_adapter:
            _youtube_comment_adapter.close()
            _youtube_comment_adapter = None
        
        _current_broadcast_id = None
        
        logger.info("[stop_streaming] Success")
        return "YouTube Live配信を停止しました。"
        
    except Exception as e:
        logger.error(f"Error in stop_streaming tool: {e}")
        return f"配信停止エラー: {str(e)}"


async def get_streaming_comments() -> str:
    """
    YouTube Live配信のコメントを取得します（Comment Adapterから）。
    
    Returns:
        コメントリスト (JSON形式)
    """
    global _youtube_comment_adapter
    
    try:
        if not _youtube_comment_adapter:
            return json.dumps([])
        
        comments = _youtube_comment_adapter.get()
        
        if not comments:
            return json.dumps([])
        
        logger.info(f"[get_streaming_comments] Retrieved {len(comments)} comments")
        return json.dumps(comments, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in get_streaming_comments tool: {e}")
        return json.dumps([])
