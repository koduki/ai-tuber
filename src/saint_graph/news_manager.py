import json
import os
from typing import Dict, Optional, List

class NewsManager:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.segments: List[Dict] = []
        self.current_index = 0
        self._load_news()

    def _load_news(self):
        if not os.path.exists(self.filepath):
            self.segments = []
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.segments = data.get("segments", [])
        except Exception as e:
            print(f"Error loading news from {self.filepath}: {e}")
            self.segments = []

    def get_next_segment(self) -> Optional[Dict]:
        if self.current_index < len(self.segments):
            return self.segments[self.current_index]
        return None

    def mark_completed(self):
        if self.current_index < len(self.segments):
            self.current_index += 1

    def has_next(self) -> bool:
        return self.current_index < len(self.segments)
