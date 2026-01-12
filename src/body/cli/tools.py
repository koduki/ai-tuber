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
    """
    inputs = io_adapter.get_inputs()
    if not inputs:
        return "No new comments."
    return "\n".join(inputs)
