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
        script_path = os.path.join(os.path.dirname(__file__), 'youtube_comment_fetcher.py')
        self.process = subprocess.Popen(
            ['python', script_path, video_id], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1,
            env=os.environ.copy()  # 環境変数を子プロセスに渡す（YOUTUBE_API_KEY等）
        )
        self.q: queue.Queue = queue.Queue()
        self.error_q: queue.Queue = queue.Queue()
        
        # stdout監視スレッド（コメント取得用）
        self.thread = threading.Thread(target=self.enqueue_output, args=(self.process.stdout, self.q))
        self.thread.daemon = True
        self.thread.start()
        
        # stderr監視スレッド（エラー検出用）
        self.error_thread = threading.Thread(target=self.enqueue_output, args=(self.process.stderr, self.error_q))
        self.error_thread.daemon = True
        self.error_thread.start()
        
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
        
        # エラー出力をチェック
        while not self.error_q.empty():
            line = self.error_q.get_nowait()
            if not line:
                continue
            
            line = line.strip()
            if line.startswith("DEBUG: "):
                logger.debug(f"YouTube comment subprocess: {line[7:]}")
            elif line.startswith("INFO: "):
                logger.info(f"YouTube comment subprocess: {line[6:]}")
            elif line.startswith("WARNING: "):
                logger.warning(f"YouTube comment subprocess: {line[9:]}")
            elif line.startswith("ERROR: "):
                logger.error(f"YouTube comment subprocess: {line[7:]}")
            else:
                # プレフィックスがない場合でも、予期せぬエラーの可能性を考慮して警告する
                logger.warning(f"YouTube comment subprocess (unprefixed): {line}")

        
        # コメントを取得
        while not self.q.empty():
            line = self.q.get_nowait()
            if line:
                try:
                    comment_data = json.loads(line.strip())
                    if "error" in comment_data:
                        logger.error(f"YouTube API error: {comment_data['error']}")
                    else:
                        new_comments.append(comment_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse comment JSON: {e}, line: {line.strip()}")
        return new_comments

    def close(self):
        """サブプロセスを終了させる"""
        self.process.terminate()
        self.process.wait()
        logger.info("Closed YouTube comment adapter")
