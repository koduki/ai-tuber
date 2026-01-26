"""MCP tools for body-desktop service"""
import logging
import json
from . import voice, obs, youtube

logger = logging.getLogger(__name__)


async def speak(text: str, style: str = "normal") -> str:
    """
    視聴者に対してテキストを発話します。
    
    Args:
        text: 発話するテキスト
        style: 発話スタイル (normal, happy, sad, angry)
        
    Returns:
        実行結果メッセージ
    """
    try:
        # 音声を生成して共有ボリュームに保存
        file_path = await voice.generate_and_save(text, style)
        
        # OBS経由で音声を再生
        await obs.refresh_media_source("voice", file_path)
        
        logger.info(f"[speak] '{text}' (style: {style})")
        return f"発話完了: {text[:20]}..."
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
