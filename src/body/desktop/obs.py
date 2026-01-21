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

# Emotion to source name mapping (matching main branch OBS scene collection)
EMOTION_MAP = {
    "neutral": "normal",
    "happy": "joyful",
    "joyful": "joyful",
    "fun": "fun",
    "sad": "normal",  # main branch doesn't have sad, use normal
    "sorrow": "normal",
    "angry": "angry",
}

# Global WebSocket client
ws_client: Optional[obsws] = None


async def connect() -> bool:
    """
    OBS WebSocketに接続します。
    既に関係がある場合は接続状態を確認し、切断されている場合は再接続します。
    
    Returns:
        接続成功の場合True
    """
    global ws_client
    
    # すでにクライアントが存在する場合
    if ws_client is not None:
        try:
            # 接続状態をテストするために簡単なリクエストを送る
            ws_client.call(obs_requests.GetVersion())
            return True
        except Exception:
            # 接続が切れている場合はクリーンアップして再接続へ
            logger.info("OBS connection lost, attempting to reconnect...")
            try:
                ws_client.disconnect()
            except:
                pass
            ws_client = None
    
    try:
        logger.info(f"Connecting to OBS at {OBS_HOST}:{OBS_PORT}")
        ws_client = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        ws_client.connect()
        logger.info("Connected to OBS WebSocket")
        return True
    except Exception as e:
        logger.debug(f"Failed to connect to OBS: {e}")
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
    # 接続を確実にする
    if not await connect():
        logger.error(f"Cannot refresh media source '{source_name}': OBS not connected")
        return False
    
    # パスが絶対パスであることを確認
    abs_path = os.path.abspath(file_path)
    
    try:
        # 1. メディアソースの設定を更新
        ws_client.call(obs_requests.SetInputSettings(
            inputName=source_name,
            inputSettings={"local_file": abs_path},
            overlay=True
        ))
        
        # 2. ソースを確実に表示状態にする（非表示だと再生されない場合があるため）
        # シーンアイテムIDではなく名前で指定する場合、SetSceneItemEnabledの代わりに
        # 他の手段が必要な場合もありますが、まずは再生命令を優先
        
        # 3. 再生を最初から開始 (Restart)
        # OBS WebSocket v5 API: TriggerMediaInputAction
        try:
            ws_client.call(obs_requests.TriggerMediaInputAction(
                inputName=source_name,
                mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
            ))
            logger.info(f"Triggered restart for media source '{source_name}'")
        except Exception as e:
            logger.warning(f"Failed to trigger media restart (might be v4 protocol): {e}")
            # v4互換のためのフォールバック (RestartMedia)
            try:
                ws_client.call(obs_requests.RestartMedia(sourceName=source_name))
            except:
                pass

        logger.info(f"Refreshed media source '{source_name}' with file: {abs_path}")
        return True
    except Exception as e:
        logger.warning(f"Error refreshing media source (first attempt): {e}")
        
        # 接続が切れた可能性があるので再接続を試みる
        await disconnect()
        if await connect():
            try:
                ws_client.call(obs_requests.SetInputSettings(
                    inputName=source_name,
                    inputSettings={"local_file": abs_path},
                    overlay=True
                ))
                logger.info(f"Refreshed media source '{source_name}' on second attempt")
                return True
            except Exception as e2:
                logger.error(f"Error refreshing media source (final attempt): {e2}")
        
        return False
