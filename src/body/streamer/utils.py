import os
import logging

logger = logging.getLogger(__name__)

def ensure_youtube_secrets():
    """Ensure that YouTube secret files exist if provided via environment variables."""
    try:
        # クライアントシークレット
        secret_json = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
        secret_path = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "/secret/google_client_secret.json")
        if secret_json:
            # Remove UTF-8 BOM if present (happens sometimes with PowerShell)
            if secret_json.startswith('\ufeff'):
                secret_json = secret_json[1:]
            os.makedirs(os.path.dirname(secret_path), exist_ok=True)
            with open(secret_path, "w") as f:
                f.write(secret_json)
            logger.info(f"Written YOUTUBE_CLIENT_SECRET_JSON to {secret_path}")
        
        # トークンキャッシュ
        token_json = os.getenv("YOUTUBE_TOKEN_JSON")
        token_path = os.getenv("YOUTUBE_TOKEN_PATH", "/secret/yt_token.json")
        if token_json:
            # Remove UTF-8 BOM if present
            if token_json.startswith('\ufeff'):
                token_json = token_json[1:]
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, "w") as f:
                f.write(token_json)
            logger.info(f"Written YOUTUBE_TOKEN_JSON to {token_path}")
    except Exception as e:
        logger.error(f"Failed to ensure YouTube secrets: {e}")
