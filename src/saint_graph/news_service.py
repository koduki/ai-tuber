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
        """Markdownファイルからニュース項目をロードします。GCSから取得可能な場合は優先的に使用します。"""
        import re
        from .config import logger

        self.items = []
        
        # GCSからのダウンロードを試行
        gcs_bucket = os.getenv("GCS_BUCKET_NAME")
        temp_path = None
        
        if gcs_bucket:
            try:
                import tempfile
                from google.cloud import storage
                
                # 一時ファイルにダウンロード
                temp_fd, temp_path = tempfile.mkstemp(suffix=".md")
                os.close(temp_fd)
                
                storage_client = storage.Client()
                bucket = storage_client.bucket(gcs_bucket)
                blob = bucket.blob("news/news_script.md")
                blob.download_to_filename(temp_path)
                
                logger.info(f"GCS から news_script.md をダウンロードしました: gs://{gcs_bucket}/news/news_script.md")
                file_to_read = temp_path
            except Exception as e:
                logger.warning(f"GCS からのダウンロードに失敗しました ({e})。ローカルファイルを使用します。")
                temp_path = None
                file_to_read = self.data_path
        else:
            file_to_read = self.data_path
        
        try:
            with open(file_to_read, 'r', encoding='utf-8') as f:
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
                     logger.debug(f"Loaded item '{title}' (Content length: {len(body)})")
            
            source = f"GCS (gs://{gcs_bucket}/news/news_script.md)" if temp_path else self.data_path
            logger.info(f"NewsService loaded {len(self.items)} items from {source}")

        except Exception as e:
            logger.error(f"Error parsing news markdown: {e}")
            self.items = []
        finally:
            # 一時ファイルのクリーンアップ
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
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
