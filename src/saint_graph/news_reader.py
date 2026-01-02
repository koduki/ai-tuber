import os
import glob
import re
from typing import List, Optional

class NewsReader:
    def __init__(self, news_dir: str):
        self.news_dir = news_dir

    def get_latest_news_chunks(self) -> Optional[List[str]]:
        """
        data/news/ 配下の最新のMarkdownを取得し、
        読み上げ単位（段落）のリストとして返します。
        """
        # Ensure directory exists
        if not os.path.exists(self.news_dir):
            return None

        files = glob.glob(os.path.join(self.news_dir, "*.md"))
        if not files:
            return None

        # 最新ファイルを取得
        latest_file = max(files, key=os.path.getmtime)

        with open(latest_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 空行(2つ以上の改行)で分割してチャンク化
        chunks = re.split(r'\n\s*\n', content)
        return [c.strip() for c in chunks if c.strip()]
