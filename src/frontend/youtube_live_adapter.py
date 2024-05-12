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
        token_file = "C:\\Users\\koduki\\.secret\\token.json"
        
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
                    'C:\\Users\\koduki\\.secret\\secret.json', scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        youtube = build('youtube', 'v3', credentials=creds)
        return youtube

    # Step 3: Create a YouTube live broadcast
    def create_broadcast(self, youtube, title, description, scheduledStartTime, privacy_status="private"):
        """Create a live broadcast on YouTube."""
        insert_broadcast_response = youtube.liveBroadcasts().insert(
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
        
        return insert_broadcast_response


# if __name__ == "__main__":
#     ytlive = YoutubeLiveAdapter()
#     youtube_client = ytlive.authenticate_youtube()
#     broadcast_response = ytlive.create_broadcast(youtube_client, "Hello World", "こんにいてゃ", '2024-05-30T00:00:00.000Z')
# from src.frontend.youtube_live_adapter import YoutubeLiveAdapter
# ytlive = YoutubeLiveAdapter()
# youtube_client = ytlive.authenticate_youtube()
# broadcast_response = ytlive.create_broadcast(youtube_client, "Hello World", "こんにいてゃ", '2024-05-30T00:00:00.000Z')



# import obsws_python as obs
# obs_password='oFdoUpmc34Ohy6lt'
# client = obs.ReqClient(host='localhost', port=4455, password=obs_password, timeout=3)
# resp = client.get_version()

# client.get_stream_service_settings().stream_service_settings
# resp
# client.start_stream()
# client.set_stream_service_settings("rtmp_common", x)



#     # ここからはOBSで良い
#     #stream_response = create_stream(youtube_client)
#     #bind_response = bind_broadcast(youtube_client, broadcast_response['id'], stream_response['id'])

# {'broadcast_id': broadcast_response["id"], 'bwtest': False, 'key': '35av-1ehq-6apb-wwyj-4v2u', 'protocol': 'RTMPS', 'server': 'rtmps://a.rtmps.youtube.com:443/live2', 'service': 'YouTube - RTMPS', 'stream_id': '25jWtoLv0erx4WAidUqXgQ1715422441289464'}
# {'broadcast_id': 'jwMQtvCsfOI',            'bwtest': False, 'key': '5cq7-dwud-6fb8-vrs6-8hpk', 'protocol': 'RTMPS', 'server': 'rtmps://a.rtmps.youtube.com:443/live2', 'service': 'YouTube - RTMPS', 'stream_id': '25jWtoLv0erx4WAidUqXgQ1617262815568304'}
# {'broadcast_id': broadcast_response["id"], 'bwtest': False, 'key': 'hzhj-1jmd-pjk7-ybm1-0yuk', 'protocol': 'RTMPS', 'server': 'rtmps://a.rtmps.youtube.com:443/live2', 'service': 'YouTube - RTMPS', 'stream_id': '25jWtoLv0erx4WAidUqXgQ1715425009404882'}


# x={'broadcast_id': broadcast_response["id"], 'bwtest': False, 'key': '5cq7-dwud-6fb8-vrs6-8hpk', 'protocol': 'RTMPS', 'server': 'rtmps://a.rtmps.youtube.com:443/live2', 'service': 'YouTube - RTMPS', 'stream_id': '25jWtoLv0erx4WAidUqXgQ1617262815568304'}


# >>> client.get_stream_service_settings().stream_service_settings
# {'broadcast_id': 'X6PjK8CxbSs', 'bwtest': False, 'key': '5cq7-dwud-6fb8-vrs6-8hpk', 'protocol': 'RTMPS', 'server': 'rtmps://a.rtmps.youtube.com:443/live2', 'service': 'YouTube - RTMPS', 'stream_id': '25jWtoLv0erx4WAidUqXgQ1617262815568304'}
# >>>

# >>> client.get_stream_service_settings().stream_service_settings
# {'broadcast_id': 'X6PjK8CxbSs', 'bwtest': False, 'key': '5cq7-dwud-6fb8-vrs6-8hpk', 'protocol': 'RTMPS', 'server': 'rtmps://a.rtmps.youtube.com:443/live2', 'service': 'YouTube - RTMPS', 'stream_id': '25jWtoLv0erx4WAidUqXgQ1715425009404882'}
# >>>


# def create_stream(youtube, title="New Stream", description="Stream Description", format="720p", resolution="720p"):
#     """Create a live stream on YouTube with specified format and resolution."""
#     insert_stream_response = youtube.liveStreams().insert(
#         part="snippet,cdn",
#         body=dict(
#             snippet=dict(
#                 title=title,
#                 description=description
#             ),
#             cdn=dict(
#                 format=format,
#                 resolution=resolution,  # 解像度を指定
#                 frameRate="30fps",
#                 ingestionType="rtmp"
#             )
#         )
#     ).execute()
    
#     return insert_stream_response

# # Step 5: Bind the live stream to the broadcast
# def bind_broadcast(youtube, broadcast_id, stream_id):
#     """Bind the live stream to the broadcast."""
#     bind_broadcast_response = youtube.liveBroadcasts().bind(
#         part="id,contentDetails",
#         id=broadcast_id,
#         streamId=stream_id
#     ).execute()
    
#     return bind_broadcast_response