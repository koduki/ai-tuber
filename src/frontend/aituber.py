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
        # self.scheduler.add_job(self.task_short_talk, 'interval', seconds=60)

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

    def syscall(self, message):
        reply = self.ai.say_chat({"speaker":"system", "message":message})
        self.voice_q.put(reply)    

    def exec(self):
        self.comments = YouTubeCommentAdapter(self.video_id)
        self.scheduler.start()
        print("Start AITuber.")

        import time

        import datetime
        today = datetime.date.today().strftime("%Y/%m/%d")
        self.syscall(f"今日は{today}です。朝活配信として適当な出だしの雑談をしてください。今日の日付や季節にちなんだ話題が良いです。雑談は500文字程度。雑談の後は天気予報を話すので、続けやすい締めにしてください。出だしは「みなのものおはよう。紅月れんなのじゃ。朝活配信をやっていくぞ。」です。")
        time.sleep(32)

        from backend.weather_api import weather_all_japan_api
        weather = weather_all_japan_api()
        self.syscall(f"今日は{today}です。次の情報を元に全国の天気の解説してください。出だし「まずは今日の天気じゃ」です。天気の情報を元に300文字程度でアドバイスや小話をして、「この後は為替とその辺の話じゃ」で締めてください。{weather}")
        time.sleep(53)
        
        from backend.finantial_tool import get_finance_index
        idx = get_finance_index()
        self.syscall(f"今日の為替や株価を次の情報を元に解説してください。気になるポイントを経済の知識と照らし合わせてコメントしてください。出だしは「つづいて経済の話をしよう」です。締めは「みんな儲かっとるかの？」です。{idx}")
        time.sleep(42)
        
        from backend.breaking_news_tool import get_news_by_rss
        r1 = get_news_by_rss("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
        r2 = get_news_by_rss("https://news.yahoo.co.jp/rss/topics/domestic.xml")
        combined = [frozenset(d.items()) for d in r1 + r2]
        unique_dicts = [dict(fs) for fs in set(combined)]
        self.syscall(f"「本日の世の中の動き」として、次のニュースの見出しを読み上げて、それぞれ感想を視聴者に語ってください。出だしは「それでは今日の世の中の動きをすこしみてみるかの」です。見出しを読み上げた後に総括を400文字でしてください。{unique_dicts}")
        time.sleep(42)
        
        from backend.memorial_day_tool import get_memorial
        memorial = get_memorial()
        self.syscall(f"今日は「{memorial}」です。関連する話を500文字で話して。出だしは「最後に今日は何の日？のコーナーじゃ。今日は」です")
        time.sleep(50)

        self.syscall(f"朝の配信の締めをしてください。「ハッピーハッキング」で終わってください。")


    def set_broadcast_id(self, video_id):
        self.video_id = video_id

