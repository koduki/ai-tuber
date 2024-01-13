import time
import datetime
import queue
import concurrent.futures
import asyncio

from .voicevox_adapter import VoicevoxAdapter
from .play_sound import PlaySound
from .obs_adapter import ObsAdapter
from .youtube_comment_adapter import YouTubeCommentAdapter

class App:
    def __init__(self, ai) -> None:
        self.ai = ai
        # self.play_sound = PlaySound("スピーカー (Realtek(R) Audio)")
        self.play_sound = PlaySound("CABLE Input")
        self.voicevox_adapter = VoicevoxAdapter()

        self.obs = ObsAdapter()
        self.obs.visible_avater("normal")
        self.obs.visible_llm(ai.llm_model)

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
        # data, rate = self._task_gen_voice(text)
        # self.obs.visible_avater(emotion)
        # self.play_sound.play_sound(data, rate)
        # self.obs.visible_avater("normal")
        xs = text.split("。")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # タスクをスケジュール
            print("voice")
            futures = [executor.submit(self._task_gen_voice, x) for x in xs]
            print("/voice")

            # 結果を待機
            for future in futures:
                print("say")
                # print(future.result())
                data, rate = future.result()
                print("/say")
                self.obs.visible_avater(emotion)
                self.play_sound.play_sound(data, rate)
                self.obs.visible_avater("normal")

    def show_error(self, e):
        print(e)
        print(e.__traceback__)

    def task_chat(self, q):
        while True:
            time.sleep(1)
            for c in self.comments.get():
                print(f"{c.datetime} [{c.author.name}]: {c.message}")
                try:
                    reply = self.ai.say_chat(c.message)
                    print("step1")
                    q.put(reply)
                    print("step1-1")
                except Exception as e:
                    self.show_error(e)

    def task_short_talk(self, q):
        while True:
            try:
                time.sleep(60*3)
                reply = self.ai.say_short_talk()
                print("step2")
                q.put(reply)
                print("step2-2")
            except Exception as e:
                self.show_error(e)  

    def task_voice(self, q):
        while True:
            try:
                time.sleep(1)
                if not q.empty():
                    print("step3")
                    reply = q.get()
                    print("step4")
                    self.voice(reply)
                    print("/step4")
                    q.task_done()
            except Exception as e:
                self.show_error(e)

    async def task_system(self):
        from aioconsole import ainput
        
        while True:
            print("step5")
            syscmd = await ainput()
            print("step5-2")
            if syscmd == "quit" or syscmd == "q":
                print(syscmd)
                exit(0)
            elif syscmd == "use_gemini":
                self.ai.chLLM("gemini")
                self.obs.visible_llm(self.ai.llm_model)
            elif syscmd == "use_gpt4":
                self.ai.chLLM("gpt4")
                self.obs.visible_llm(self.ai.llm_model)

    async def _exec(self):
        # q = asyncio.Queue()
        # t1 = asyncio.create_task(self.task_chat(q))
        # t2 = asyncio.create_task(self.task_short_talk(q))
        # t3 = asyncio.create_task(self.task_voice(q))
        # t4 = asyncio.create_task(self.task_system())

        q = queue.Queue()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(self.task_voice, q)
            executor.submit(self.task_short_talk, q)
            executor.submit(self.task_chat, q)

        # await t1
        # await t2
        # await t3
        # await t4

    def exec(self, video_id):
        self.comments = YouTubeCommentAdapter(video_id)
        print("Ready. YouTubeにコメントしてね。終了時は「quit」または「q」と入力してください。")

        self.voice({"character_reply":"良く来たの。今日は何をするのじゃ？", "current_emotion":"joyful"})

        asyncio.run(self._exec())
