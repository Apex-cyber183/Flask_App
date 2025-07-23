from flask import Flask, render_template, request, jsonify
from puzzles import puzzles

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_puzzle/<int:index>")
def get_puzzle(index):
    if index < len(puzzles):
        return jsonify(puzzles[index])
    else:
        return jsonify({"done": True})

@app.route("/check_answer", methods=["POST"])
def check_answer():
    data = request.get_json()
    index = data.get("index")
    answer = data.get("answer")
    correct = puzzles[index]["correct"]
    return jsonify({"correct": answer == correct})

if __name__ == "__main__":
    app.run(debug=True)
