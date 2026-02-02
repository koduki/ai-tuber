"""YouTube Live comment adapter using subprocess"""
import subprocess
import threading
import queue
import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class YouTubeCommentAdapter:
    """Adapter for fetching YouTube Live comments using subprocess"""
    
    def __init__(self, video_id: str):
        """
        Initialize the comment adapter.
        
        Args:
            video_id: YouTube video/broadcast ID
        """
        script_path = os.path.join(os.path.dirname(__file__), 'fetch_comments.py')
        self.process = subprocess.Popen(
            ['python', script_path, video_id], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        self.q: queue.Queue = queue.Queue()
        self.thread = threading.Thread(target=self.enqueue_output, args=(self.process.stdout, self.q))
        self.thread.daemon = True  # スレッドがデーモン化され、メインプログラム終了時に終了
        self.thread.start()
        logger.info(f"Started YouTube comment adapter for video: {video_id}")

    def enqueue_output(self, out, queue: queue.Queue):
        """Read output lines and enqueue them."""
        for line in iter(out.readline, ''):
            queue.put(line)
        out.close()

    def get(self) -> List[Dict]:
        """
        サブプロセスからデータを取得してリストで返す
        
        Returns:
            List of comment dictionaries
        """
        new_comments = []
        while not self.q.empty():
            line = self.q.get_nowait()  # キューからデータを取得
            if line:
                try:
                    new_comments.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse comment JSON: {e}")
        return new_comments

    def close(self):
        """サブプロセスを終了させる"""
        self.process.terminate()
        self.process.wait()
        logger.info("Closed YouTube comment adapter")
