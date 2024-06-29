import subprocess
import threading
import queue
import os
import json

class YouTubeCommentAdapter:
    def __init__(self, video_id):
        script_path = os.path.join(os.path.dirname(__file__), 'fetch_comments.py')
        self.process = subprocess.Popen(['python', script_path, video_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self.enqueue_output, args=(self.process.stdout, self.q))
        self.thread.daemon = True  # スレッドがデーモン化され、メインプログラム終了時に終了
        self.thread.start()

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, ''):
            queue.put(line)
        out.close()

    def get(self):
        """サブプロセスからデータを取得してリストで返す"""
        new_comments = []
        while not self.q.empty():
            line = self.q.get_nowait()  # キューからデータを取得
            if line:
                new_comments.append(json.loads(line.strip()))
        return new_comments

    def close(self):
        """サブプロセスを終了させる"""
        self.process.terminate()
        self.process.wait()