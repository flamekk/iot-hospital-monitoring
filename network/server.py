from flask import Flask, request, jsonify
from datetime import datetime
import os
import csv
import json

app = Flask(__name__)

OUTPUT_FILE = os.path.join("results", "received_data.csv")

os.makedirs("results", exist_ok=True)


def save_received_record(record):
    file_exists = os.path.exists(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


@app.route("/ingest", methods=["POST"])
def ingest():
    receive_time = datetime.now().isoformat()
    payload = request.get_json()

    if payload is None:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    if isinstance(payload, list):
        for item in payload:
            record = {
                "receive_time": receive_time,
                "payload": json.dumps(item)
            }
            save_received_record(record)
        return jsonify({"status": "success", "received_count": len(payload)}), 200

    else:
        record = {
            "receive_time": receive_time,
            "payload": json.dumps(payload)
        }
        save_received_record(record)
        return jsonify({"status": "success", "received_count": 1}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
