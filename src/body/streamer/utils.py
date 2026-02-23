import os
import logging

logger = logging.getLogger(__name__)

def ensure_youtube_secrets():
    """
    Ensure that YouTube secrets are available.
    Note: Secrets are now handled in-memory in YoutubeLiveAdapter to support 
    cloud-native environments without local filesystem access.
    """
    secret_json = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
    token_json = os.getenv("YOUTUBE_TOKEN_JSON")
    
    if secret_json or token_json:
        logger.info("YouTube secrets detected in environment variables (in-memory mode active)")
    else:
        logger.info("No YouTube secrets JSON found in environment; falling back to file paths if available")

