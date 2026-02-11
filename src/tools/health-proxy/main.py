import os
import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cloud Run structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/check")
def check():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing url parameter"}), 400
    
    try:
        response = requests.get(url, timeout=5)
        result = {
            "status": response.status_code,
            "url": url,
            "ready": response.status_code == 200
        }
        logger.info(f"Health check: url={url}, status={response.status_code}, ready={result['ready']}")
        return jsonify(result), 200
    except Exception as e:
        result = {
            "error": str(e),
            "url": url,
            "ready": False
        }
        logger.warning(f"Health check failed: url={url}, error={str(e)}")
        return jsonify(result), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
