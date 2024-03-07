import os
import sys

from flask import Flask, render_template, request, jsonify
from celery import Celery

from backend.chatai import ChatAI
from frontend.app import App

secret_path = f"{os.environ['HOMEPATH']}/.secret/"
os.environ["OPENAI_API_KEY"] = open(secret_path + "openai.txt", "r").read()
os.environ["OPENAI_API_KEY"] = open(secret_path + "gemini.txt", "r").read()
os.environ["OBS_WS_PASSWORD"] = open(secret_path + "obs.txt", "r").read()

# AI
llm_model = sys.argv[1] if len(sys.argv) > 1 else 'gemini'
ai = ChatAI(llm_model)

# video_id = input() # "YOUR_VIDEO_ID"

# app2 = App(ai)
# app.exec(video_id)

# Web
app = Flask(__name__)

from flask import Flask
from celery import Celery

app = Flask(__name__)

# 新しい設定キーを使用
app.config.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    # Celery 5.xではbroker_connection_retry_on_startupのような設定は
    # 直接Celery設定で指定する必要があります（後述）
)

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['broker_url']
    )
    celery.conf.update(app.config)
    celery.conf.broker_connection_retry_on_startup = True
    # タスクの定義時にFlaskアプリケーションコンテキストを使用するためのフック
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# 定期的なタスクの定義
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # 10秒ごとにhello_celeryタスクを実行
    sender.add_periodic_task(5.0, hello_celery.s(), name='Print Hello every 5 seconds')

@celery.task
def hello_celery():
    print("Hello Celery!")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hello", methods=["POST"])
def hello():
    name = request.json["name"]
    return jsonify({"message": "Hello, {}!".format(name)})

@app.route("/start", methods=["POST"])
def start():
    name = request.json["name"]
    
    # app2.exec("videoid")
    return jsonify({"message": "Start Stream, {}!".format(name)})

if __name__ == "__main__":
    app.run(debug=True)