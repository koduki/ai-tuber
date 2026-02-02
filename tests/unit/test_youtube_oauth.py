import os
import pytest
import json
from unittest.mock import patch, MagicMock
from google.oauth2.credentials import Credentials


class TestYouTubeOAuth:
    """YouTube OAuth 認証のテスト
    
    Note: このテストは実際の秘密情報を使用せず、モックデータで動作します。
    """
    
    def test_oauth_credentials_from_env(self):
        """環境変数からOAuth認証情報を正しく読み込めること"""
        # モックのトークン情報
        token_json = json.dumps({
            "token": "ya29.mock_access_token",
            "refresh_token": "1//mock_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "mock-client-id.apps.googleusercontent.com",
            "client_secret": "MOCK-secret",
            "scopes": ["https://www.googleapis.com/auth/youtube"],
            "expiry": "2026-02-03T00:00:00Z"
        })
        
        with patch.dict(os.environ, {"YOUTUBE_TOKEN_JSON": token_json}):
            # 環境変数からトークン情報を読み込む（fetch_comments.py の実装と同じ）
            youtube_token_json = os.getenv("YOUTUBE_TOKEN_JSON", "")
            assert youtube_token_json != ""
            
            token_info = json.loads(youtube_token_json)
            
            # Credentials オブジェクトを作成
            creds = Credentials.from_authorized_user_info(
                token_info,
                scopes=token_info.get('scopes')
            )
            
            # 検証
            assert creds.token == "ya29.mock_access_token"
            assert creds.refresh_token == "1//mock_refresh_token"
            assert "https://www.googleapis.com/auth/youtube" in creds.scopes
    
    def test_oauth_credentials_missing(self):
        """認証情報が無い場合、空文字列が返されること"""
        with patch.dict(os.environ, {}, clear=True):
            youtube_token_json = os.getenv("YOUTUBE_TOKEN_JSON", "")
            
            # 環境変数が無い場合は空文字列
            assert youtube_token_json == ""
    
    def test_oauth_scope_from_token(self):
        """トークンに含まれるスコープを正しく使用できること"""
        token_info = {
            "token": "ya29.mock",
            "refresh_token": "1//mock",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "mock.apps.googleusercontent.com",
            "client_secret": "mock-secret",
            "scopes": ["https://www.googleapis.com/auth/youtube"]
        }
        
        # スコープがトークンから正しく取得される
        scopes = token_info.get('scopes', ["https://www.googleapis.com/auth/youtube"])
        assert scopes == ["https://www.googleapis.com/auth/youtube"]
        
        # Credentials 作成時にスコープが使用される
        creds = Credentials.from_authorized_user_info(token_info, scopes=scopes)
        assert creds.scopes == scopes
    
    def test_oauth_with_youtube_scope(self):
        """youtube スコープ（読み取り専用を含む）が使用できること"""
        # youtube スコープは youtube.readonly を包含する
        token_info = {
            "token": "ya29.mock",
            "refresh_token": "1//mock",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "mock.apps.googleusercontent.com",
            "client_secret": "mock-secret",
            "scopes": ["https://www.googleapis.com/auth/youtube"]
        }
        
        creds = Credentials.from_authorized_user_info(
            token_info,
            scopes=token_info.get('scopes')
        )
        
        # youtube スコープが設定されている
        assert "https://www.googleapis.com/auth/youtube" in creds.scopes
    
    def test_oauth_json_parsing_error(self):
        """不正なJSON形式の場合、適切にエラーが発生すること"""
        invalid_json = "{ invalid json"
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
    
    def test_client_secret_from_env(self):
        """クライアントシークレットも環境変数から読み込めること"""
        client_secret_json = json.dumps({
            "installed": {
                "client_id": "mock-id.apps.googleusercontent.com",
                "project_id": "mock-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "MOCK-secret",
                "redirect_uris": ["http://localhost"]
            }
        })
        
        with patch.dict(os.environ, {"YOUTUBE_CLIENT_SECRET_JSON": client_secret_json}):
            secret_json = os.getenv("YOUTUBE_CLIENT_SECRET_JSON", "")
            assert secret_json != ""
            
            secret_info = json.loads(secret_json)
            assert "installed" in secret_info
            assert secret_info["installed"]["client_id"] == "mock-id.apps.googleusercontent.com"
