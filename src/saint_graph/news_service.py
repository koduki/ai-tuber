import json
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NewsItem:
    id: str
    category: str
    title: str
    content: str

class NewsService:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.items: List[NewsItem] = []
        self.current_index = 0

    def load_news(self):
        """Loads news items from the Markdown file."""
        import re
        if not os.path.exists(self.data_path):
            # Try relative path as fallback
            alt_path = os.path.join(os.getcwd(), "data", "news", "news_script.md")
            if os.path.exists(alt_path):
                self.data_path = alt_path
            else:
                # Debug info: list what's in the directory
                data_dir = os.path.dirname(self.data_path)
                found_files = []
                if os.path.exists(data_dir):
                    found_files = os.listdir(data_dir)
                elif os.path.exists("/app/data"):
                    found_files = [f"at /app/data: {os.listdir('/app/data')}"]
                
                print(f"DEBUG: News data not found at {self.data_path}. CWD: {os.getcwd()}, Dir content: {found_files}")
                raise FileNotFoundError(f"News data not found at {self.data_path}")
        
        self.items = []
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use bracket for spaces to be explicit. Catch ## at start of line or following newline(s)
            sections = re.split(r'[\r\n]+##[ \t]*', '\n' + content)
            
            for i, section in enumerate(sections):
                section = section.strip()
                if not section or i == 0: # Skip the intro/header
                    continue
                
                lines = section.split('\n', 1)
                title = lines[0].strip()
                body = lines[1].strip() if len(lines) > 1 else ""
                
                if title:
                     self.items.append(NewsItem(
                         id=f"news_{i}",
                         category="News",
                         title=title,
                         content=body or "(No content)"
                     ))
                     print(f"DEBUG: Loaded item '{title}' (Content length: {len(body)})")
            
            print(f"DEBUG: NewsService loaded {len(self.items)} items from {self.data_path}")
            if not self.items:
                 print(f"DEBUG: File content summary (first 200 chars): {content[:200]}...")

        except Exception as e:
            print(f"Error parsing news markdown: {e}")
            self.items = []
        
        self.current_index = 0

    def has_next(self) -> bool:
        """Checks if there are more news items to read."""
        return self.current_index < len(self.items)

    def get_next_item(self) -> Optional[NewsItem]:
        """Returns the next news item and advances the index."""
        if not self.has_next():
            return None
        
        item = self.items[self.current_index]
        self.current_index += 1
        return item

    def peek_current_item(self) -> Optional[NewsItem]:
        """Returns the current news item without advancing (if we need to retry)."""
        if self.current_index >= len(self.items):
            return None
        return self.items[self.current_index]

    def reset(self):
        """Resets the reading progress."""
        self.current_index = 0
