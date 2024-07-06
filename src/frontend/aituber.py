import time
import datetime
import queue
import concurrent.futures

from .voicevox_adapter import VoicevoxAdapter
from .play_sound import PlaySound
from .obs_adapter import ObsAdapter
from .youtube_comment_adapter import YouTubeCommentAdapter
from apscheduler.schedulers.background import BackgroundScheduler

class AITuber:
    def __init__(self, ai) -> None:
        self.ai = ai
        self.play_sound = PlaySound("pulse")
        self.voicevox_adapter = VoicevoxAdapter()

        self.obs = ObsAdapter()
        self.obs.visible_avater("normal")
        self.obs.visible_llm(ai.llm_model)

        # ボイスキュー
        self.voice_q = queue.Queue()

        # APSchedulerの初期化とジョブの追加
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.task_chat, 'interval', seconds=1)
        self.scheduler.add_job(self.task_voice, 'interval', seconds=1)
        self.scheduler.add_job(self.task_short_talk, 'interval', seconds=60)

    def _task_gen_voice(self, text):
        ss = time.perf_counter()
        data, rate = self.voicevox_adapter.get_voice(text)
        se = time.perf_counter()
        print("voice response(sec): " + str(se - ss))

        return data, rate    
    
    def voice(self, msg):
        text = msg["character_reply"]
        emotion = msg["current_emotion"]
        print(f"{datetime.datetime.now()} [紅月れん]: {text}")

        xs = text.split("。")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # タスクをスケジュール
            print("voice")
            futures = [executor.submit(self._task_gen_voice, x) for x in xs]
            print("/voice")

            # 結果を待機
            for future in futures:
                print("say")
                data, rate = future.result()
                print("/say")
                self.obs.visible_avater(emotion)
                self.play_sound.play_sound(data, rate)
                self.obs.visible_avater("normal")

    def show_error(self, e):
        print(e)
        print(e.__traceback__)

    def task_chat(self):
        for c in self.comments.get():
            print(f"{c['datetime']} [{c['author']}]: {c['message']}")
            try:
                reply = self.ai.say_chat({"speaker":c["author"], "message":c["message"]})
                print("step1")
                print(reply)
                self.voice_q.put(reply)
                print("/step1")
            except Exception as e:
                self.show_error(e)

    def task_short_talk(self):
        try:
            reply = self.ai.say_short_talk()
            print("step2")
            self.voice_q.put(reply)
            print("/step2")
        except Exception as e:
            self.show_error(e)  

    def task_voice(self):
        try:
            if not self.voice_q.empty():
                reply = self.voice_q.get()
                print("step3")
                self.voice(reply)
                print("/step3")
                self.voice_q.task_done()
        except Exception as e:
            self.show_error(e)

    def close(self):
        print("Shutting down scheduler...")
        self.scheduler.shutdown(wait=False)
        print("Shutting down comments...")
        self.comments.close()

    def exec(self):
        self.comments = YouTubeCommentAdapter(self.video_id)
        self.scheduler.start()
        print("Start AITuber.")

        import time

        self.voice({"character_reply":"みなのものおはよう。紅月れんなのじゃ。朝活配信をやっていくぞ。", "current_emotion":"joyful"})
        time.sleep(1)

        self.voice({"character_reply":"まずは今日の天気からじゃな。", "current_emotion":"joyful"})
        self.voice({"character_reply":"札幌の天気は晴れ、東京の天気は32度、福岡は雨じゃな。", "current_emotion":"joyful"})
        self.voice({"character_reply":"2日も梅雨前線が西日本から東日本に延びて、", "current_emotion":"joyful"})
        self.voice({"character_reply":"活動の活発な状態が続く見込みのようじゃから注意が必要じゃぞ。", "current_emotion":"joyful"})
        self.voice({"character_reply":"天気に関して聞きたいことは何かあるのか？", "current_emotion":"joyful"})


    def set_broadcast_id(self, video_id):
        self.video_id = video_id

