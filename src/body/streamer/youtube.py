"""YouTube Live comment fetcher"""
import os
import logging
import threading
import queue
from typing import List, Dict, Optional
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# YouTube configuration from environment
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_LIVE_CHAT_ID = os.getenv("YOUTUBE_LIVE_CHAT_ID", "")
POLLING_INTERVAL = int(os.getenv("YOUTUBE_POLLING_INTERVAL", "5"))

# Comment queue (thread-safe)
comment_queue: queue.Queue = queue.Queue()

# Global state
_polling_thread: Optional[threading.Thread] = None
_stop_polling = threading.Event()


def _fetch_comments_loop(live_chat_id: str, api_key: str):
    """
    バックグラウンドでコメントをポーリングします。
    
    Args:
        live_chat_id: YouTube Live Chat ID
        api_key: YouTube Data API v3 キー
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    next_page_token = None
    
    logger.info(f"Started YouTube comment polling (chat_id: {live_chat_id})")
    
    while not _stop_polling.is_set():
        try:
            request = youtube.liveChatMessages().list(
                liveChatId=live_chat_id,
                part='snippet,authorDetails',
                pageToken=next_page_token
            )
            response = request.execute()
            
            # 新しいコメントをキューに追加
            for item in response.get('items', []):
                comment = {
                    'author': item['authorDetails']['displayName'],
                    'message': item['snippet']['displayMessage'],
                    'timestamp': item['snippet']['publishedAt']
                }
                comment_queue.put(comment)
                logger.debug(f"New comment from {comment['author']}: {comment['message']}")
            
            # 次のポーリングまで待機
            next_page_token = response.get('nextPageToken')
            polling_interval_ms = response.get('pollingIntervalMillis', POLLING_INTERVAL * 1000)
            time.sleep(polling_interval_ms / 1000.0)
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            time.sleep(POLLING_INTERVAL)
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            time.sleep(POLLING_INTERVAL)
    
    logger.info("Stopped YouTube comment polling")


def start_comment_polling():
    """
    バックグラウンドスレッドでコメントポーリングを開始します。
    """
    global _polling_thread
    
    if not YOUTUBE_API_KEY or not YOUTUBE_LIVE_CHAT_ID:
        logger.warning("YouTube API credentials not configured. Comment polling disabled.")
        return
    
    if _polling_thread is not None and _polling_thread.is_alive():
        logger.warning("Comment polling already running")
        return
    
    _stop_polling.clear()
    _polling_thread = threading.Thread(
        target=_fetch_comments_loop,
        args=(YOUTUBE_LIVE_CHAT_ID, YOUTUBE_API_KEY),
        daemon=True
    )
    _polling_thread.start()
    logger.info("YouTube comment polling thread started")


def stop_comment_polling():
    """コメントポーリングを停止します。"""
    global _polling_thread
    
    if _polling_thread is None or not _polling_thread.is_alive():
        logger.warning("Comment polling not running")
        return
    
    _stop_polling.set()
    _polling_thread.join(timeout=5.0)
    _polling_thread = None
    logger.info("Comment polling stopped")


async def get_new_comments() -> List[Dict[str, str]]:
    """
    キューから新規コメントを取得します。
    
    Returns:
        コメントのリスト (各コメントは author, message, timestamp を含む)
    """
    comments = []
    
    while not comment_queue.empty():
        try:
            comment = comment_queue.get_nowait()
            comments.append(comment)
        except queue.Empty:
            break
    
    if comments:
        logger.info(f"Retrieved {len(comments)} new comments")
    
    return comments
