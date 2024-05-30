import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request 

class YoutubeLiveAdapter:
    def __init__(self) -> None:
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
                flow = InstalledAppFlow.from_client_secrets_file(
                    'C:\\Users\\koduki\\.secret\\google_client_secret.json', scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        youtube = build('youtube', 'v3', credentials=creds)
        return youtube
    
    def create_broadcast(self, youtube, title, description, scheduledStartTime, privacy_status="private"):
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
                    enableAutoStart=True
                ),
                status=dict(
                    privacyStatus=privacy_status
                )
            )
        ).execute()
        
        return res

    def create_stream(self, youtube, title):
        res = youtube.liveStreams().insert(
            part="snippet,cdn",
            body=dict(
                snippet=dict(
                    title=title
                ),
                cdn=dict(
                    format="1080p",
                    ingestionType="rtmp",
                    resolution="1080p",  # 解像度を追加
                    frameRate="30fps"  # フレームレートを追加
                )
            )
        ).execute()

        return res

    def bind_broadcast_to_stream(self, youtube, broadcast_id, stream_id):
        bind_response = youtube.liveBroadcasts().bind(
            part="id,contentDetails",
            id=broadcast_id,
            streamId=stream_id
        ).execute()

        return bind_response

    def stop_broadcast(self, youtube, broadcast_id):
        """Stop a live broadcast on YouTube."""

        res = youtube.liveBroadcasts().transition(
            broadcastStatus="complete",
            id=broadcast_id,
            part="id,status"
        ).execute()
        
        return res

if __name__ == "__main__":
    from frontend.youtube_live_adapter import YoutubeLiveAdapter
    ytlive = YoutubeLiveAdapter()

    youtube_client = ytlive.authenticate_youtube()

    title = "Hello World4"
    desc  = "こんにいてゃ"
    start_date = '2024-06-30T00:00:00.000Z'
    broadcast_response = ytlive.create_broadcast(youtube_client, title, desc, start_date)
    stream_response = ytlive.create_stream(youtube_client, title + "_Stream")
    bind_response = ytlive.bind_broadcast_to_stream(youtube_client, broadcast_response['id'], stream_response['id'])

    # Extract the stream key:
    stream_key = stream_response['cdn']['ingestionInfo']['streamName']


    import obsws_python as obs
    obs_password='j85l4lc0yoAlh7Ou'
    client = obs.ReqClient(host='localhost', port=4455, password=obs_password, timeout=3)

    settings = client.get_stream_service_settings().stream_service_settings
    settings['key'] = stream_key

    client.set_stream_service_settings("rtmp_common", settings)
    client.start_stream()

    client.stop_stream()
    stop_response = ytlive.stop_broadcast(youtube_client, broadcast_response['id'])
