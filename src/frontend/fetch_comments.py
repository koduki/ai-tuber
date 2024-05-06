import pytchat
import json
import sys

def main(video_id):
    chat = pytchat.create(video_id=video_id)
    while chat.is_alive():
        for chatdata in chat.get().sync_items():
            comment_data = {
                "datetime": chatdata.datetime,
                "author": chatdata.author.name,
                "message": chatdata.message
            }
            # JSON形式で出力
            print(json.dumps(comment_data, ensure_ascii=False))
            sys.stdout.flush()  # 標準出力のバッファをフラッシュ

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_comments.py [video_id]")
        sys.exit(1)
    video_id = sys.argv[1]
    main(video_id)