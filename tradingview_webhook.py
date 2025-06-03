from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"[WEBHOOK RECEIVED] {data}")

    if not data or "action" not in data or "side" not in data or "symbol" not in data:
        print("[ERROR] Missing 'action', 'side', or 'symbol'")
        return jsonify({"error": "Missing action, side, or symbol"}), 400

    action = data["action"].lower()
    side = data["side"].lower()
    symbol = data["symbol"].upper()

    allowed_symbols = {"BONK_USDT", "PENGU_USDT", "GROK_USDT"}
    if symbol not in allowed_symbols:
        print(f"[ERROR] Invalid symbol: {symbol}")
        return jsonify({"error": f"Invalid symbol: must be one of {allowed_symbols}"}), 400

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

        print(f"[ACTION] Opening {side} position on {symbol} with vol={vol}, lev={leverage}")
        subprocess.Popen(["python3", "open_trades.py", side_map[side], vol, leverage, symbol])

    elif action == "close":
        print(f"[ACTION] Closing {side} position on {symbol}...")
        subprocess.Popen(["python3", "close_all.py", side_map[side], symbol])

    else:
        print(f"[ERROR] Invalid action: {action}")
        return jsonify({"error": "Invalid action: must be 'open' or 'close'"}), 400

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    print("[TRADINGVIEW WEBHOOK] Server starting...")
    import os

    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
