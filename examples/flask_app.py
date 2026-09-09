from flask import Flask, jsonify
from requestguard import Algorithm, RateLimitExceeded, limit

app = Flask(__name__)

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(exc):
    return jsonify(exc.detail), 429

@app.route("/hello")
@limit(requests=3, window=30, algorithm=Algorithm.LEAKY_BUCKET)
def hello_route():
    return {"message": "Hello!"}


if __name__ == "__main__":
    app.run(debug=True)
