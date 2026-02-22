"""Subprocess script for fetching YouTube Live chat comments"""
import sys
import json
import time
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def fetch_comments(video_id: str):
    """
    Fetch comments from YouTube Live chat and output as JSON lines.
    
    Args:
        video_id: YouTube broadcast/video ID
    """
    # YouTube OAuth configuration from environment
    youtube_token_json = os.getenv("YOUTUBE_TOKEN_JSON", "")
    
    if not youtube_token_json:
        error_msg = "YOUTUBE_TOKEN_JSON not set"
        print(json.dumps({"error": error_msg}), flush=True)
        print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
        return
    
    print(f"DEBUG: Starting comment fetch for video {video_id} using OAuth", file=sys.stderr, flush=True)
    
    try:
        # Parse OAuth credentials from JSON string
        token_info = json.loads(youtube_token_json)
        
        # Use the scopes from the existing token to avoid refresh errors
        # The token was granted with 'youtube' scope which includes read access
        creds = Credentials.from_authorized_user_info(
            token_info,
            scopes=token_info.get('scopes', ["https://www.googleapis.com/auth/youtube"])
        )
        
        # Build YouTube API client with OAuth credentials
        youtube = build('youtube', 'v3', credentials=creds)
        print(f"DEBUG: Successfully authenticated with OAuth", file=sys.stderr, flush=True)
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse YOUTUBE_TOKEN_JSON: {e}"
        print(json.dumps({"error": error_msg}), flush=True)
        print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
        return
    except Exception as e:
        error_msg = f"Failed to create OAuth credentials: {e}"
        print(json.dumps({"error": error_msg}), flush=True)
        print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
        return
    
    # Get the live chat ID from the video (with retry logic)
    live_chat_id = None
    max_retries = 10
    retry_interval = 10
    
    for attempt in range(max_retries):
        try:
            video_response = youtube.videos().list(
                part='liveStreamingDetails',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                print(json.dumps({"error": f"Video {video_id} not found"}), flush=True)
                time.sleep(retry_interval)
                continue
            
            live_streaming_details = video_response['items'][0].get('liveStreamingDetails', {})
            live_chat_id = live_streaming_details.get('activeLiveChatId')
            
            if live_chat_id:
                print(f"DEBUG: Found live chat ID: {live_chat_id}", file=sys.stderr, flush=True)
                break
            else:
                print(f"DEBUG: Live chat not active yet (attempt {attempt + 1}/{max_retries})", file=sys.stderr, flush=True)
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
                    
        except HttpError as e:
            error_msg = f"YouTube API error getting live chat ID: {e}"
            print(json.dumps({"error": error_msg}), flush=True)
            print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                return
    
    if not live_chat_id:
        error_msg = f"No active live chat found after {max_retries} attempts"
        print(json.dumps({"error": error_msg}), flush=True)
        print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
        return

    
    next_page_token = None
    polling_interval = 5
    
    print(f"DEBUG: Starting comment polling loop", file=sys.stderr, flush=True)
    
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
            error_msg = f"API error while fetching comments: {e}"
            print(json.dumps({"error": error_msg}), flush=True)
            print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
            time.sleep(5)
        except KeyboardInterrupt:
            print("DEBUG: Keyboard interrupt received, exiting", file=sys.stderr, flush=True)
            break
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(json.dumps({"error": error_msg}), flush=True)
            print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: youtube_comment_fetcher.py <video_id>"}), flush=True)
        sys.exit(1)
    
    video_id = sys.argv[1]
    fetch_comments(video_id)
