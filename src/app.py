import os
import sys

from flask import Flask, render_template, request, jsonify

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

app2 = App(ai)
# app.exec(video_id)

# Web
app = Flask(__name__)

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
    
    app2.exec("videoid")
    return jsonify({"message": "Start Stream, {}!".format(name)})

if __name__ == "__main__":
    app.run(debug=True)