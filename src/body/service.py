"""Body サービスの共通インターフェース (ABC)

CLI / Streamer 両モードが準拠すべき抽象基底クラスを定義します。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BodyServiceBase(ABC):
    """Body サービスが実装すべき共通インターフェース。"""

    @abstractmethod
    async def speak(self, text: str, style: str = "neutral", speaker_id: Optional[int] = None) -> str:
        """テキストを発話します。"""
        ...

    @abstractmethod
    async def change_emotion(self, emotion: str) -> str:
        """アバターの表情（感情）を変更します。"""
        ...

    @abstractmethod
    async def get_comments(self) -> str:
        """コメントを取得します。JSON 文字列（List[Dict]）を返します。"""
        ...

    @abstractmethod
    async def start_broadcast(self, config: Optional[Dict[str, Any]] = None) -> str:
        """録画または配信を開始します。"""
        ...

    @abstractmethod
    async def wait_for_queue(self) -> str:
        """すべての処理が完了するまで待機します。"""
        ...
