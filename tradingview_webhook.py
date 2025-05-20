from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"[WEBHOOK RECEIVED] {data}")

    if not data or "action" not in data or "side" not in data:
        print("[ERROR] Missing 'action' or 'side'")
        return jsonify({"error": "Missing action or side"}), 400

    action = data["action"].lower()
    side = data["side"].lower()
    side_map = {"long": "1", "short": "3"}

    if side not in side_map:
        print(f"[ERROR] Invalid side: {side}")
        return jsonify({"error": "Invalid side: must be 'long' or 'short'"}), 400

    if action == "open":
        if "vol" not in data or "leverage" not in data:
            print("[ERROR] Missing 'vol' or 'leverage' for open action")
            return jsonify({"error": "Missing 'vol' or 'leverage' for open action"}), 400

        vol = str(data["vol"])
        leverage = str(data["leverage"])

        print(f"[ACTION] Opening {side} position with vol={vol}, lev={leverage}")
        subprocess.Popen(["python3", "open_trades.py", side_map[side], vol, leverage])

    elif action == "close":
        print(f"[ACTION] Closing {side} position...")
        subprocess.Popen(["python3", "close_all.py", side_map[side]])

    else:
        print(f"[ERROR] Invalid action: {action}")
        return jsonify({"error": "Invalid action: must be 'open' or 'close'"}), 400

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    print("[TRADINGVIEW WEBHOOK] Server starting...")
    app.run(host="0.0.0.0", port=5050, debug=True)
