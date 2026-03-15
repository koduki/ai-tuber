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
    "sad": "sad",
    "sorrow": "sad",
    "angry": "angry",
    "silent": "silent",
}

# リップシンク調整：音声が鳴り始めるまでのOBS内部遅延をミリ秒で指定
# 0.5s〜1s遅れるとのことなので、デフォルトを400ms〜800ms程度で調整可能にします
LIP_SYNC_ADJUST_MS = int(os.getenv("LIP_SYNC_ADJUST_MS", "500"))

# Global WebSocket client
ws_client: Optional[obsws] = None
_playback_event = asyncio.Event()

# Scene Item ID Cache (to avoid redundant API calls)
_source_id_cache = {}
_current_scene_name = None

def _on_media_start(event):
    """OBSからのメディア再生開始イベントを受け取るコールバック"""
    try:
        source_name = event.getInputName()
        if source_name == "voice":
            logger.info("OBS Event: 'voice' playback actually started!")
            # asyncio.Eventをセット（メインタスクの待機を解除）
            # ただし、このコールバックは別スレッドで動くため、loop.call_soon_threadsafe等が必要な場合があるが、
            # 基本的にEvent.set()はスレッドセーフなケースが多い（環境による）
            _playback_event.set()
    except Exception:
        pass

async def connect() -> bool:
    """OBS WebSocketに接続し、イベントリスナーを登録します。"""
    global ws_client
    
    # 接続確認
    if ws_client is not None:
        try:
            ws_client.call(obs_requests.GetVersion())
            return True
        except Exception:
            ws_client = None
    
    try:
        ws_client = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        ws_client.connect()
        
        # 再生開始イベント（v5）を購読
        ws_client.register(_on_media_start, "MediaInputPlaybackStarted")
        
        logger.info("Connected to OBS WebSocket and registered event listeners")
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
    ソースの表示/非表示を切り替えます（キャッシュを活用して高速化）。
    """
    global _source_id_cache, _current_scene_name
    
    if not await connect():
        return False
    
    try:
        # シーン名の取得とキャッシュのリフレッシュ
        if scene_name is None:
            if _current_scene_name is None:
                resp = ws_client.call(obs_requests.GetCurrentProgramScene())
                _current_scene_name = resp.getSceneName()
            scene_name = _current_scene_name

        # キャッシュの確認
        cache_key = f"{scene_name}:{source_name}"
        scene_item_id = _source_id_cache.get(cache_key)

        if scene_item_id is None:
            # キャッシュにない場合は取得
            scene_items = ws_client.call(obs_requests.GetSceneItemList(sceneName=scene_name))
            for item in scene_items.getSceneItems():
                item_name = item["sourceName"]
                item_id = item["sceneItemId"]
                _source_id_cache[f"{scene_name}:{item_name}"] = item_id
                if item_name == source_name:
                    scene_item_id = item_id
        
        if scene_item_id is None:
            logger.warning(f"Source '{source_name}' not found in scene '{scene_name}'")
            return False
            
        # シーンアイテムの表示/非表示を設定
        ws_client.call(obs_requests.SetSceneItemEnabled(
            sceneName=scene_name,
            sceneItemId=scene_item_id,
            sceneItemEnabled=visible
        ))
        return True
    except Exception as e:
        logger.error(f"Error setting source visibility for '{source_name}': {e}")
        # エラー時はキャッシュをクリアして次回リトライ
        _source_id_cache = {}
        _current_scene_name = None
        return False


async def set_visible_source(emotion: str) -> str:
    """
    指定された感情に対応する立ち絵ソースを表示します。
    """
    source_name = EMOTION_MAP.get(emotion, EMOTION_MAP["neutral"])
    if not await connect():
        return f"OBS接続エラー"
    
    try:
        # スレッドセーフかつ高速に実行するため、直列に実行します（キャッシュがあるので十分早いです）
        # 1. まずターゲットを表示
        await set_source_visibility(source_name, True)

        # 2. 他を非表示
        for emo_source in set(EMOTION_MAP.values()):
            if emo_source != source_name:
                await set_source_visibility(emo_source, False)
        
        return f"表情変更: {emotion}"
    except Exception as e:
        logger.error(f"Error changing emotion: {e}")
        return f"表情変更エラー: {str(e)}"


async def refresh_media_source(source_name: str, file_path: str) -> bool:
    """
    指定されたメディアソースのファイルを更新し、再生を開始します。
    
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
        
        # 2. 音量をリセットし、ミュートを解除 (v5 API)
        try:
            ws_client.call(obs_requests.SetInputVolume(inputName=source_name, inputVolumeMul=1.0))
            ws_client.call(obs_requests.SetInputMute(inputName=source_name, inputMuted=False))
        except Exception:
            pass

        # 3. OBSが設定を反映するのをわずかに待つ（高速化のため短縮）
        await asyncio.sleep(0.05)
        
        # 4. 再生をリスタート (v5 API)
        try:
            ws_client.call(obs_requests.TriggerMediaInputAction(
                inputName=source_name,
                mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
            ))
            logger.info(f"Triggered restart for media source '{source_name}'")
        except Exception as e:
            logger.warning(f"Failed to trigger media restart (might be v4 protocol): {e}")
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


async def start_recording() -> bool:
    """OBSの録画を開始します。"""
    if not await connect():
        return False
    
    try:
        response = ws_client.call(obs_requests.StartRecord())
        if response.status:
            logger.info(f"Started OBS recording: {response.status}")
            return True
        else:
            logger.warning(f"Failed to start OBS recording: {response}")
            return False
    except Exception as e:
        logger.error(f"Error starting OBS recording: {e}")
        return False


async def stop_recording() -> bool:
    """OBSの録画を停止します。"""
    if not await connect():
        return False
    
    try:
        ws_client.call(obs_requests.StopRecord())
        logger.info("Stopped OBS recording")
        return True
    except Exception as e:
        logger.error(f"Error stopping OBS recording: {e}")
        return False


async def get_record_status() -> bool:
    """録画中かどうかを確認します。"""
    if not await connect():
        return False
    
    try:
        response = ws_client.call(obs_requests.GetRecordStatus())
        return response.getOutputActive()
    except Exception as e:
        logger.error(f"Error getting OBS recording status: {e}")
        return False


async def start_streaming(stream_key: str) -> bool:
    """
    OBSのストリーミングを開始します。
    
    Args:
        stream_key: YouTube RTMP stream key
        
    Returns:
        成功の場合True
    """
    if not await connect():
        return False
    
    try:
        # Use custom RTMP for better reliability
        custom_settings = {
            "server": "rtmp://a.rtmp.youtube.com/live2",
            "key": stream_key,
            "use_auth": False
        }
        
        ws_client.call(obs_requests.SetStreamServiceSettings(
            streamServiceType="rtmp_custom",
            streamServiceSettings=custom_settings
        ))
        logger.info(f"Updated OBS stream settings with Custom RTMP and key")
        logger.info(f"Updated OBS stream settings with new key")
        
        # Start streaming
        ws_client.call(obs_requests.StartStream())
        logger.info("Started OBS streaming")
        return True
    except Exception as e:
        logger.error(f"Error starting OBS streaming: {e}")
        return False


async def stop_streaming() -> bool:
    """OBSのストリーミングを停止します。"""
    if not await connect():
        return False
    
    try:
        ws_client.call(obs_requests.StopStream())
        logger.info("Stopped OBS streaming")
        return True
    except Exception as e:
        logger.error(f"Error stopping OBS streaming: {e}")
        return False


async def get_streaming_status() -> bool:
    """ストリーミング中かどうかを確認します。"""
    if not await connect():
        return False
    
    try:
        response = ws_client.call(obs_requests.GetStreamStatus())
        return response.getOutputActive()
    except Exception as e:
        logger.error(f"Error getting OBS streaming status: {e}")
        return False

async def play_media_with_emotion(audio_source: str, file_path: str, emotion: str) -> bool:
    """
    音声の再生開始と表情の切り替えを、可能な限り同時に実行します。
    """
    if not await connect():
        return False
        
    abs_path = os.path.abspath(file_path)

    try:
        # --- 準備フェーズ ---
        # 1. 音声ソースを必ず「表示」状態にする（ミキサー消失防止）
        await set_source_visibility(audio_source, True)

        # 2. 音声ファイルの「装填」を済ませる
        ws_client.call(obs_requests.SetInputSettings(
            inputName=audio_source,
            inputSettings={"local_file": abs_path},
            overlay=True
        ))
        
        # 3. 音量/ミュート設定
        try:
            ws_client.call(obs_requests.SetInputVolume(inputName=audio_source, inputVolumeMul=1.0))
            ws_client.call(obs_requests.SetInputMute(inputName=audio_source, inputMuted=False))
        except Exception:
            pass
            
        # 4. OBS側での読み込み完了を待つ (0.1s)
        await asyncio.sleep(0.1)
        
        # --- 発火フェーズ ---
        # 5. イベントフラグをリセット
        _playback_event.clear()

        # 6. 音声再生トリガーを引く
        ws_client.call(obs_requests.TriggerMediaInputAction(
            inputName=audio_source,
            mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
        ))
        
        # 7. OBSから「再生が始まったよ！」というイベントが来るのを待つ（最大5秒）
        # これにより内部のバッファリング時間を完璧に同期させます
        try:
            logger.info("Waiting for OBS playback event...")
            await asyncio.wait_for(_playback_event.wait(), timeout=5.0)
            logger.info("Playback event received! Showing mouth movement.")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for OBS playback event. Showing mouth anyway.")

        # 8. 表情変更（口パク開始）を実行
        await set_visible_source(emotion)
        
        return True
    except Exception as e:
        logger.error(f"Error in play_media_with_emotion: {e}")
        return False
