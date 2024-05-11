import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
            part="snippet,status",
            body=dict(
                snippet=dict(
                    title=title,
                    description=description,
                    scheduledStartTime=scheduledStartTime
                ),
                status=dict(
                    privacyStatus=privacy_status
                )
            )
        ).execute()
        
        return insert_broadcast_response


if __name__ == "__main__":
    ytlive = YoutubeLiveAdapter()
    youtube_client = ytlive.authenticate_youtube()
    broadcast_response = ytlive.create_broadcast(youtube_client, "Hello World", "こんにいてゃ", '2024-05-30T00:00:00.000Z')

    # ここからはOBSで良い
    #stream_response = create_stream(youtube_client)
    #bind_response = bind_broadcast(youtube_client, broadcast_response['id'], stream_response['id'])

