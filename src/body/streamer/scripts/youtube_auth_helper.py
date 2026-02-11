"""YouTube Auth Helper Script"""
import logging
import sys
import os

# Add the project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.body.streamer.youtube_live_adapter import YoutubeLiveAdapter

def ensure_secrets():
    """Ensure that secret files exist if provided via environment variables."""
    # Matches the logic in main.py
    secret_json = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
    secret_path = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "/secret/google_client_secret.json")
    if secret_json and not os.path.exists(secret_path):
        os.makedirs(os.path.dirname(secret_path), exist_ok=True)
        with open(secret_path, "w") as f:
            f.write(secret_json)
        print(f"Written YOUTUBE_CLIENT_SECRET_JSON to {secret_path}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting YouTube Authentication Helper...")
    
    # Ensure secret files exist (e.g. from environment variables)
    ensure_secrets()
    
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
