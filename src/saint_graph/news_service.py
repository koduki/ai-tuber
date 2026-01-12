import json
import os
from dataclasses import dataclass
from typing import List, Optional

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
        self.data_path = data_path
        self.items: List[NewsItem] = []
        self.current_index = 0

    def load_news(self):
        """Markdownファイルからニュース項目をロードします。"""
        import re

        self.items = []
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
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
                     print(f"DEBUG: Loaded item '{title}' (Content length: {len(body)})")
            
            print(f"DEBUG: NewsService loaded {len(self.items)} items from {self.data_path}")

        except Exception as e:
            print(f"Error parsing news markdown: {e}")
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
