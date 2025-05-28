import hashlib
import time
import requests
import json
import sys

# === CONFIG ===
token = "WEBf0b5b0b6af6a55686f6fcce284bc690302ddcfc8283aeaefc1b08aeeaf12fa28"

def generate_content_sign(payload: dict, token: str, timestamp: str):
    payload_str = json.dumps(payload, separators=(',', ':'))
    full_md5 = hashlib.md5((token + timestamp).encode()).hexdigest()
    sliced = full_md5[7:]
    content_sign = hashlib.md5((timestamp + payload_str + sliced).encode()).hexdigest()
    return content_sign, payload_str

def open_trade(side, vol, leverage, symbol):
    payload = {
        "symbol": symbol,
        "side": side,               # 1 = long, 3 = short
        "openType": 1,
        "type": "5",
        "vol": vol,
        "leverage": leverage,
        "marketCeiling": False,
        "bboPriceType": 0,
        "priceProtect": "0"
    }

    timestamp = str(int(time.time() * 1000))
    content_sign, payload_str = generate_content_sign(payload, token, timestamp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
        "Content-time": timestamp,
        "Content-sign": content_sign,
        "Accept": "*/*"
    }

    url = "https://www.kcex.com/fapi/v1/private/order/create"
    res = requests.post(url, headers=headers, data=payload_str)

    print("Status:", res.status_code)
    print("Response:", res.text)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python open_trades.py [side: 1=long,3=short] [vol] [leverage] [symbol]")
        sys.exit(1)

    side = int(sys.argv[1])
    vol = float(sys.argv[2])
    leverage = int(sys.argv[3])
    symbol = sys.argv[4]

    open_trade(side, vol, leverage, symbol)
