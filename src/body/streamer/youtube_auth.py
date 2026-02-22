import os
import json
import logging
from typing import Optional, Tuple, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Fallback paths for local development
YOUTUBE_CLIENT_SECRET_PATH = os.path.join("data", "youtube_client_secret.json")
YOUTUBE_TOKEN_PATH = os.path.join("data", "youtube_token.json")

class YouTubeAuth:
    """Centralized authentication management for YouTube Data API v3."""

    SCOPES = ["https://www.googleapis.com/auth/youtube"]

    @classmethod
    def get_credentials(cls) -> Optional[Credentials]:
        """
        Load and return YouTube credentials from environment variables or file.
        Automatically handles BOM and basic JSON validation.
        """
        creds = None
        
        # 1. Try to load from environment variable (JSON string) first
        token_json_str = os.getenv("YOUTUBE_TOKEN_JSON")
        if token_json_str:
            try:
                # Remove UTF-8 BOM if present
                if token_json_str.startswith('\ufeff'):
                    token_json_str = token_json_str[1:]
                token_info = json.loads(token_json_str)
                # Use scopes from token or default
                scopes = token_info.get('scopes', cls.SCOPES)
                creds = Credentials.from_authorized_user_info(token_info, scopes)
                logger.info("Loaded YouTube credentials from YOUTUBE_TOKEN_JSON environment variable")
            except Exception as e:
                logger.error(f"Failed to load credentials from YOUTUBE_TOKEN_JSON: {e}")

        # 2. Fallback to file if not loaded from env
        if not creds and os.path.exists(YOUTUBE_TOKEN_PATH):
            try:
                creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_PATH, cls.SCOPES)
                logger.info(f"Loaded YouTube credentials from {YOUTUBE_TOKEN_PATH}")
            except Exception as e:
                logger.error(f"Failed to load credentials from {YOUTUBE_TOKEN_PATH}: {e}")
        
        # 3. Handle token refresh if possible
        if creds and creds.expired and creds.refresh_token:
            logger.info("YouTube token expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                logger.info("YouTube token refreshed successfully")
            except Exception as e:
                logger.warning(f"Failed to refresh YouTube token: {e}")
                # Return expired creds, higher level might choose to start OAuth flow
        
        return creds

    @classmethod
    def get_service(cls, creds: Optional[Credentials] = None) -> Any:
        """
        Build and return the YouTube service client.
        If creds is not provided, it will attempt to load them.
        """
        if not creds:
            creds = cls.get_credentials()
            
        if not creds or not creds.valid:
            raise ValueError("No valid YouTube credentials found. Authorization required.")
            
        return build('youtube', 'v3', credentials=creds)

    @classmethod
    def start_oauth_flow(cls) -> Tuple[Any, Credentials]:
        """
        Start an interactive OAuth 2.0 flow to obtain new credentials.
        This is intended for CLI use or initial setup.
        """
        flow = None
        client_secret_json_str = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
        
        if client_secret_json_str:
            try:
                if client_secret_json_str.startswith('\ufeff'):
                    client_secret_json_str = client_secret_json_str[1:]
                client_config = json.loads(client_secret_json_str)
                flow = Flow.from_client_config(
                    client_config,
                    scopes=cls.SCOPES,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                logger.info("Initialized YouTube OAuth flow from YOUTUBE_CLIENT_SECRET_JSON")
            except Exception as e:
                logger.error(f"Failed to initialize flow from YOUTUBE_CLIENT_SECRET_JSON: {e}")

        if not flow and os.path.exists(YOUTUBE_CLIENT_SECRET_PATH):
            flow = Flow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRET_PATH,
                scopes=cls.SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            logger.info(f"Initialized YouTube OAuth flow from {YOUTUBE_CLIENT_SECRET_PATH}")

        if not flow:
            raise FileNotFoundError("YouTube client secret not found in environment or file.")

        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print('\n' + '='*60)
        print('AUTHORIZATION REQUIRED FOR YOUTUBE LIVE')
        print('Please go to this URL in your browser:')
        print(f'{auth_url}')
        print('='*60 + '\n')
        
        code = input('Enter the authorization code: ')
        credential = flow.fetch_token(code=code)
        
        creds = Credentials(
            token=credential['access_token'],
            refresh_token=credential['refresh_token'],
            token_uri=flow.client_config['token_uri'],
            client_id=flow.client_config['client_id'],
            client_secret=flow.client_config['client_secret'],
            scopes=cls.SCOPES
        )

        # Save to file if path exists (optional)
        try:
            os.makedirs(os.path.dirname(YOUTUBE_TOKEN_PATH), exist_ok=True)
            with open(YOUTUBE_TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
            logger.info(f"Saved new credentials to {YOUTUBE_TOKEN_PATH}")
        except Exception as e:
            logger.warning(f"Could not save tokens to {YOUTUBE_TOKEN_PATH}: {e}")

        return cls.get_service(creds), creds
