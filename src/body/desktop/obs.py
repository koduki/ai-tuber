"""OBS WebSocket adapter for scene and source control"""
import os
import logging
from typing import Optional
import asyncio

try:
    from obswebsocket import obsws, requests as obs_requests
except ImportError:
    obs_requests = None
    obsws = None

logger = logging.getLogger(__name__)

# OBS configuration from environment
OBS_HOST = os.getenv("OBS_HOST", "obs-studio")
OBS_PORT = int(os.getenv("OBS_PORT", "4455"))
OBS_PASSWORD = os.getenv("OBS_PASSWORD", "")

# Emotion to source name mapping
EMOTION_MAP = {
    "neutral": "avatar_neutral",
    "happy": "avatar_happy",
    "joyful": "avatar_happy",
    "fun": "avatar_happy",
    "sad": "avatar_sad",
    "sorrow": "avatar_sad",
    "angry": "avatar_angry",
}

# Global WebSocket client
ws_client: Optional[obsws] = None


async def connect() -> bool:
    """
    OBS WebSocketに接続します。
    
    Returns:
        接続成功の場合True
    """
    global ws_client
    
    if ws_client is not None:
        return True
    
    try:
        logger.info(f"Connecting to OBS at {OBS_HOST}:{OBS_PORT}")
        ws_client = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        ws_client.connect()
        logger.info("Connected to OBS WebSocket")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to OBS: {e}")
        ws_client = None
        return False


async def disconnect():
    """OBS WebSocketから切断します。"""
    global ws_client
    
    if ws_client is not None:
        try:
            ws_client.disconnect()
            logger.info("Disconnected from OBS WebSocket")
        except Exception as e:
            logger.error(f"Error disconnecting from OBS: {e}")
        finally:
            ws_client = None


async def set_source_visibility(source_name: str, visible: bool, scene_name: Optional[str] = None) -> bool:
    """
    ソースの表示/非表示を切り替えます。
    
    Args:
        source_name: ソース名
        visible: 表示する場合True
        scene_name: シーン名 (Noneの場合は現在のシーン)
        
    Returns:
        成功の場合True
    """
    if not await connect():
        return False
    
    try:
        if scene_name is None:
            # 現在のシーンを取得
            current_scene = ws_client.call(obs_requests.GetCurrentProgramScene())
            scene_name = current_scene.getSceneName()
        
        # ソースの表示/非表示を設定
        ws_client.call(obs_requests.SetSceneItemEnabled(
            sceneName=scene_name,
            sceneItemId=source_name,
            sceneItemEnabled=visible
        ))
        logger.info(f"Set source '{source_name}' visibility to {visible}")
        return True
    except Exception as e:
        logger.error(f"Error setting source visibility: {e}")
        return False


async def set_visible_source(emotion: str) -> str:
    """
    指定された感情に対応する立ち絵ソースを表示します。
    他の感情ソースは非表示にします。
    
    Args:
        emotion: 感情 (neutral, happy, sad, angry)
        
    Returns:
        結果メッセージ
    """
    source_name = EMOTION_MAP.get(emotion, EMOTION_MAP["neutral"])
    
    if not await connect():
        return f"OBS接続エラー"
    
    try:
        # すべての感情ソースを非表示
        for emo_source in EMOTION_MAP.values():
            if emo_source != source_name:
                await set_source_visibility(emo_source, False)
        
        # 指定された感情ソースを表示
        await set_source_visibility(source_name, True)
        
        logger.info(f"Changed emotion to: {emotion} (source: {source_name})")
        return f"表情変更: {emotion}"
    except Exception as e:
        logger.error(f"Error changing emotion: {e}")
        return f"表情変更エラー: {str(e)}"


async def refresh_media_source(source_name: str, file_path: str) -> bool:
    """
    メディアソースのファイルパスを更新して再生します。
    
    Args:
        source_name: メディアソース名
        file_path: 新しいファイルパス
        
    Returns:
        成功の場合True
    """
    if not await connect():
        return False
    
    try:
        # メディアソースの設定を更新
        ws_client.call(obs_requests.SetInputSettings(
            inputName=source_name,
            inputSettings={"local_file": file_path},
            overlay=True
        ))
        logger.info(f"Refreshed media source '{source_name}' with file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error refreshing media source: {e}")
        return False
