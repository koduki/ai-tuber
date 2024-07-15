import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request 

class YoutubeLiveAdapter:
    def __init__(self) -> None:
        self.youtube_client = self.authenticate_youtube()
        pass
    
    # Step 2: Set up credentials and YouTube API client
    def authenticate_youtube(self):
        """Authenticate to the YouTube API and return the API client."""
        # Scopes required by the API
        scopes = ["https://www.googleapis.com/auth/youtube"]
        
        # File for storing user access tokens
        token_file = "/secret/yt_token.json"
        
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = Flow.from_client_secrets_file(
                    '/secret/google_client_secret.json',
                    scopes=scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                auth_url, _ = flow.authorization_url(prompt='consent')
                print('Please go to this URL: {}'.format(auth_url))
                code = input('Enter the authorization code: ')
                credential = flow.fetch_token(code=code)
                creds = Credentials(
                    token=credential['access_token'],
                    refresh_token=credential['refresh_token'],
                    token_uri=flow.client_config['token_uri'],
                    client_id=flow.client_config['client_id'],
                    client_secret=flow.client_config['client_secret'],
                    scopes=scopes
                )

            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        youtube = build('youtube', 'v3', credentials=creds)
        return youtube
    
    def create_live(self, title, description, scheduledStartTime, thumbnail_path, privacy_status="private"):
        broadcast_response = self._create_broadcast(self.youtube_client, title, description, scheduledStartTime, privacy_status)
        thumbnail_response = self._set_thumbnail(self.youtube_client, broadcast_response['id'], thumbnail_path)
        stream_response = self._create_stream(self.youtube_client, title + "_Stream")
        bind_response = self._bind_broadcast_to_stream(self.youtube_client, broadcast_response['id'], stream_response['id'])
        return {"broadcast":broadcast_response, "thumbnail":thumbnail_response, "stream":stream_response, "bind":bind_response}
    
    def _create_broadcast(self, youtube, title, description, scheduledStartTime, privacy_status="private"):
        """Create a live broadcast on YouTube."""
        res = youtube.liveBroadcasts().insert(
            part="snippet,status,contentDetails",
            body=dict(
                snippet=dict(
                    title=title,
                    description=description,
                    scheduledStartTime=scheduledStartTime
                ),
                contentDetails=dict(
                    enableAutoStart=True,
                    latencyPreference="ultraLow"  # 超低遅延
                ),
                status=dict(
                    privacyStatus=privacy_status
                )
            )
        ).execute()
         
        return res
    
    def _set_thumbnail(self, youtube, broadcast_id, thumbnail_path):
        """Set the thumbnail for a YouTube live broadcast."""
        request = youtube.thumbnails().set(
            videoId=broadcast_id,
            media_body=thumbnail_path
        )
        response = request.execute()
        
        return response
    
    def _create_stream(self, youtube, title):
        res = youtube.liveStreams().insert(
            part="snippet,cdn",
            body=dict(
                snippet=dict(
                    title=title
                ),
                cdn=dict(
                    format="720p",
                    ingestionType="rtmp",
                    resolution="720p",  # 解像度を720pに設定
                    frameRate="30fps"  # フレームレートを追加
                )
            )
        ).execute()
        
        return res
    
    def _bind_broadcast_to_stream(self, youtube, broadcast_id, stream_id):
        bind_response = youtube.liveBroadcasts().bind(
            part="id,contentDetails",
            id=broadcast_id,
            streamId=stream_id
        ).execute()
    
        return bind_response
    
    def stop_live(self, broadcast_id):
        """Stop a live broadcast on YouTube."""
        
        res = self.youtube_client.liveBroadcasts().transition(
            broadcastStatus="complete",
            id=broadcast_id,
            part="id,status"
        ).execute()
        
        return res

if __name__ == "__main__":
    from frontend.youtube_live_adapter import YoutubeLiveAdapter
    ytlive = YoutubeLiveAdapter()

    youtube_client = ytlive.authenticate_youtube()

    title = "【AI配信テスト】test 【#紅月れん】"
    description = """AITuber「紅月恋（れん）」の配信テストです。良ければコメントで話しかけてみてください。

    # クレジット＆テクノロジー
    キャラ絵はStable Diffusionで生成しました。
    LLMはChatGPTまたはGemini Proを利用しています。
    BGMはSuno.aiで作成しました。
    音声は「VOICEVOX:猫使ビィ」を利用させていただいています。
    - https://voicevox.hiroshiba.jp/
    - https://nekotukarb.wixsite.com/nekonohako/%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84
    """
    start_date = '2024-06-30T00:00:00.000Z'
    thumbnail_path = '/workspaces/ai-tuber/obs_data/ai_normal.png'

    live_response = ytlive.create_live(youtube_client, title, description, start_date, thumbnail_path, "private")

    # Extract the stream key:
    stream_key = live_response['stream']['cdn']['ingestionInfo']['streamName']


    import obsws_python as obs
    obs_password='j85l4lc0yoAlh7Ou'
    client = obs.ReqClient(host='localhost', port=4455, password=obs_password, timeout=3)

    settings = client.get_stream_service_settings().stream_service_settings
    settings['key'] = stream_key

    client.set_stream_service_settings("rtmp_common", settings)
    client.start_stream()

    client.stop_stream()
    stop_response = ytlive.stop_live(youtube_client, broadcast_response['id'])
