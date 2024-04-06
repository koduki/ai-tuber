from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

def scheduled_task():
    print("Hello World")

# APSchedulerの初期化とジョブの追加
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_task, 'interval', seconds=5)
scheduler.start()

@app.route('/')
def index():
    return "Flask and APScheduler Example!"

if __name__ == '__main__':
    try:
        app.run(use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # アプリケーションが終了する際に、スケジューラも適切に停止させる
        scheduler.shutdown()
