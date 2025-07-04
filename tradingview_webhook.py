from flask import Flask, request, jsonify
import subprocess
import threading  # ✅ only added import

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    def logic():
        print(f"[WEBHOOK RECEIVED] {data}")

        if not data or "action" not in data or "side" not in data or "symbol" not in data:
            print("[ERROR] Missing 'action', 'side', or 'symbol'")
            return

        action = data["action"].lower()
        side = data["side"].lower()
        symbol = data["symbol"].upper()

        allowed_symbols = {"BONK_USDT", "SHIB_USDT", "DOGE_USDT", "TON_USDT", "POPCAT_USDT"}
        if symbol not in allowed_symbols:
            print(f"[ERROR] Invalid symbol: {symbol}")
            return

        side_map = {"long": "1", "short": "3"}

        if side not in side_map:
            print(f"[ERROR] Invalid side: {side}")
            return

        if action == "open":
            print(f"[ACTION] Opening {side} position on {symbol}")
            subprocess.Popen(["python3", "open_trades.py", side_map[side], symbol])

        elif action == "close":
            print(f"[ACTION] Closing {side} position on {symbol}...")
            subprocess.Popen(["python3", "close_all.py", side_map[side], symbol])

        else:
            print(f"[ERROR] Invalid action: {action}")
            return

    threading.Thread(target=logic).start()  # ✅ run logic async
    return jsonify({"status": "success"}), 200  # ✅ respond immediately

if __name__ == "__main__":
    print("[TRADINGVIEW WEBHOOK] Server starting...")
    import os
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
