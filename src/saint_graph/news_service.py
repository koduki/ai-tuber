import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional
from infra.storage_client import create_storage_client

@dataclass
class NewsItem:
    """ニュース項目のデータモデル"""
    id: str
    category: str
    title: str
    content: str

class NewsService:
    """Markdown形式のニュース原稿を管理するサービス"""
    def __init__(self, data_path: str):
        """
        NewsServiceを初期化します。
        
        Args:
            data_path: ニュース原稿の論理パス（例: "news/news_script.md"）
        """
        self.data_path = data_path
        self.items: List[NewsItem] = []
        self.current_index = 0
        self.storage = create_storage_client()

    def load_news(self):
        """Markdownファイルからニュース項目をロードします。"""
        from .config import logger

        self.items = []
        
        # ストレージから読み出し
        try:
            content = self.storage.read_text(key=self.data_path)
            logger.info(f"NewsService loaded content from {self.data_path} using {self.storage.__class__.__name__}")
            
            # 区切り文字（##）に基づいてセクションを分割。セクション冒頭はスキップ。
            sections = re.split(r'[\r\n]+##[ \t]*', '\n' + content)
            
            for i, section in enumerate(sections):
                section = section.strip()
                if not section or i == 0:
                    continue
                
                # 最初の一行をタイトル、残りを本文として抽出
                lines = section.split('\n', 1)
                title = lines[0].strip()
                body = lines[1].strip() if len(lines) > 1 else ""
                
                if title:
                     self.items.append(NewsItem(
                         id=f"news_{i}",
                         category="News",
                         title=title,
                         content=body or "(本文なし)"
                     ))
                     logger.debug(f"Loaded item '{title}' (Content length: {len(body)})")
            
            logger.info(f"NewsService successfully parsed {len(self.items)} items.")

        except Exception as e:
            logger.error(f"Error parsing news markdown: {e}")
            self.items = []
        
        self.current_index = 0

    def has_next(self) -> bool:
        """未読のニュース項目があるか確認します。"""
        return self.current_index < len(self.items)

    def get_next_item(self) -> Optional[NewsItem]:
        """次のニュース項目を取得し、インデックスを進めます。"""
        if not self.has_next():
            return None
        
        item = self.items[self.current_index]
        self.current_index += 1
        return item

    def peek_current_item(self) -> Optional[NewsItem]:
        """現在のニュース項目を、インデックスを進めずに参照します。"""
        if self.current_index >= len(self.items):
            return None
        return self.items[self.current_index]

    def reset(self):
        """ニュースの進行状況をリセットします。"""
        self.current_index = 0
