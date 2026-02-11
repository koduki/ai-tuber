"""YouTube Auth Helper Script"""
import logging
import sys
import os

from src.body.streamer.youtube_live_adapter import YoutubeLiveAdapter
from src.body.streamer.utils import ensure_youtube_secrets


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting YouTube Authentication Helper...")
    
    # Ensure secret files exist (e.g. from environment variables)
    ensure_youtube_secrets()
    
    try:
        adapter = YoutubeLiveAdapter()
        # This will trigger the OAuth flow if credentials are missing or expired
        youtube_client = adapter.authenticate_youtube()
        
        # Access credentials from the build client
        creds = youtube_client._http.credentials if hasattr(youtube_client, "_http") else None
        
        if creds:
            print("\n" + "="*60)
            print("NEW YOUTUBE_TOKEN_JSON (Copy this to your .env file):")
            print("="*60)
            print(creds.to_json())
            print("="*60 + "\n")
            
        logger.info("Authentication check/refresh completed successfully!")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
