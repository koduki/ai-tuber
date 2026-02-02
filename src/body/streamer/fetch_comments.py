"""Subprocess script for fetching YouTube Live chat comments"""
import sys
import json
import time
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def fetch_comments(video_id: str):
    """
    Fetch comments from YouTube Live chat and output as JSON lines.
    
    Args:
        video_id: YouTube broadcast/video ID
    """
    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        print(json.dumps({"error": "YOUTUBE_API_KEY not set"}), flush=True)
        return
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # Get the live chat ID from the video
    try:
        video_response = youtube.videos().list(
            part='liveStreamingDetails',
            id=video_id
        ).execute()
        
        if not video_response.get('items'):
            print(json.dumps({"error": f"Video {video_id} not found"}), flush=True)
            return
        
        live_chat_id = video_response['items'][0]['liveStreamingDetails'].get('activeLiveChatId')
        if not live_chat_id:
            print(json.dumps({"error": "No active live chat found"}), flush=True)
            return
            
    except HttpError as e:
        print(json.dumps({"error": f"YouTube API error: {e}"}), flush=True)
        return
    
    next_page_token = None
    polling_interval = 5
    
    # Polling loop
    while True:
        try:
            request = youtube.liveChatMessages().list(
                liveChatId=live_chat_id,
                part='snippet,authorDetails',
                pageToken=next_page_token
            )
            response = request.execute()
            
            # Output new comments as JSON lines
            for item in response.get('items', []):
                comment = {
                    'author': item['authorDetails']['displayName'],
                    'message': item['snippet']['displayMessage'],
                    'timestamp': item['snippet']['publishedAt']
                }
                print(json.dumps(comment), flush=True)
            
            # Update next page token and polling interval
            next_page_token = response.get('nextPageToken')
            polling_interval = response.get('pollingIntervalMillis', 5000) / 1000.0
            
            time.sleep(polling_interval)
            
        except HttpError as e:
            print(json.dumps({"error": f"API error: {e}"}), flush=True)
            time.sleep(5)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({"error": f"Unexpected error: {e}"}), flush=True)
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: fetch_comments.py <video_id>"}), flush=True)
        sys.exit(1)
    
    video_id = sys.argv[1]
    fetch_comments(video_id)
