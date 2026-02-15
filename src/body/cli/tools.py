"""
MCPツール実装モジュール。
発話、感情変更、コメント取得の各ツールを提供します。
"""
from typing import Optional
from .io_adapter import io_adapter


async def speak(text: str, style: Optional[str] = None, **kwargs) -> str:
    """
    指定されたテキストを標準出力に表示（発話）します。
    """
    style_str = f" ({style})" if style else ""
    io_adapter.write_output(f"\n[AI{style_str}]: {text}")
    return "Speaking completed"


async def change_emotion(emotion: str) -> str:
    """
    アバターの感情を変更します。
    （注：現在はログ出力のみですが、将来的にLive2D等の制御を想定しています）
    """
    return f"Emotion changed to {emotion}"


async def get_comments() -> str:
    """
    キューに蓄積されたユーザーコメントを取得します。
    
    Returns:
        コメントリスト (JSON形式)
    """
    import json
    inputs = io_adapter.get_inputs()
    if not inputs:
        return json.dumps([])
    
    # body-streamerの形式に合わせて、辞書のリストとして返す
    comments = [{"author": "User", "message": line} for line in inputs]
    return json.dumps(comments, ensure_ascii=False)


async def start_broadcast(config: dict = None) -> str:
    """
    配信/録画を開始します。
    CLI モードでは何もしません（ログ出力のみ）。
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[CLI] start_broadcast called (no-op in CLI mode)")
    return "CLI mode: broadcast start skipped"


async def stop_broadcast() -> str:
    """
    配信/録画を停止します。
    CLI モードでは何もしません（ログ出力のみ）。
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[CLI] stop_broadcast called (no-op in CLI mode)")
    return "CLI mode: broadcast stop skipped"
