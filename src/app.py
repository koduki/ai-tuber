from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hello", methods=["POST"])
def hello():
    name = request.json["name"]
    return jsonify({"message": "Hello, {}!".format(name)})

if __name__ == "__main__":
    app.run(debug=True)