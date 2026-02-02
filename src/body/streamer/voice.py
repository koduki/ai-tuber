"""VoiceVox adapter for speech synthesis"""
import os
import logging
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

# VoiceVox configuration from environment
VOICEVOX_HOST = os.getenv("VOICEVOX_HOST", "voicevox")
VOICEVOX_PORT = int(os.getenv("VOICEVOX_PORT", "50021"))
VOICEVOX_BASE_URL = f"http://{VOICEVOX_HOST}:{VOICEVOX_PORT}"

# Shared audio directory
VOICE_DIR = Path("/app/shared/voice")
VOICE_DIR.mkdir(parents=True, exist_ok=True)

# Speaker ID mapping (style -> speaker_id)
SPEAKER_MAP = {
    "normal": 1,
    "happy": 2,
    "sad": 9,
    "angry": 6,
}


def get_wav_duration(file_path: str) -> float:
    """
    Calculate WAV file duration in seconds.
    
    Args:
        file_path: Path to WAV file
        
    Returns:
        Duration in seconds
    """
    import wave
    try:
        with wave.open(file_path, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
            logger.debug(f"WAV duration for {file_path}: {duration:.2f}s")
            return duration
    except Exception as e:
        logger.error(f"Error calculating WAV duration: {e}")
        # Fallback: estimate ~0.1s per character for Japanese text
        return 3.0  # Default fallback


async def generate_speech(text: str, speaker_id: int = 1) -> bytes:
    """
    VoiceVox APIを使用して音声を合成します。
    
    Args:
        text: 合成するテキスト
        speaker_id: 話者ID
        
    Returns:
        音声データ (WAV形式)
    """
    async with httpx.AsyncClient() as client:
        # Step 1: クエリの生成
        query_response = await client.post(
            f"{VOICEVOX_BASE_URL}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=10.0
        )
        query_response.raise_for_status()
        audio_query = query_response.json()
        
        # Step 2: 音声合成
        synthesis_response = await client.post(
            f"{VOICEVOX_BASE_URL}/synthesis",
            params={"speaker": speaker_id},
            json=audio_query,
            timeout=30.0
        )
        synthesis_response.raise_for_status()
        
        return synthesis_response.content


async def save_to_shared_volume(audio_data: bytes, filename: str) -> str:
    """
    音声データを共有ボリュームに保存します。
    
    Args:
        audio_data: 音声データ
        filename: ファイル名
        
    Returns:
        保存されたファイルのパス
    """
    file_path = VOICE_DIR / filename
    file_path.write_bytes(audio_data)
    if file_path.exists():
        size = file_path.stat().st_size
        logger.info(f"Saved audio to {file_path} (size: {size} bytes)")
    else:
        logger.error(f"Failed to verify written file: {file_path}")
    return str(file_path)


async def generate_and_save(text: str, style: str = "normal") -> tuple[str, float]:
    """
    音声を生成して共有ボリュームに保存します。
    
    Args:
        text: 発話テキスト
        style: 発話スタイル (normal, happy, sad, angry)
        
    Returns:
        (file_path, duration) のタプル
    """
    speaker_id = SPEAKER_MAP.get(style, 1)
    logger.info(f"Generating speech: '{text}' with style '{style}' (speaker {speaker_id})")
    
    try:
        audio_data = await generate_speech(text, speaker_id)
        filename = f"speech_{hash(text) % 10000}.wav"
        file_path = await save_to_shared_volume(audio_data, filename)
        duration = get_wav_duration(file_path)
        return file_path, duration
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        raise
