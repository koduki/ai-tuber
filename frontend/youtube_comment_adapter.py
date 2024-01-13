import pytchat

class YouTubeCommentAdapter:
    def __init__(self, video_id) -> None:
        self.chat = pytchat.create(video_id=video_id)
    
    def get(self):
        if self.chat.is_alive():
            return self.chat.get().sync_items()
        else:
            return []
        