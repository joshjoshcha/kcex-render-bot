import hashlib
import time
import requests
import json
import sys

# === USER CONFIG ===
symbol = "BONK_USDT"
token = "WEBf0b5b0b6af6a55686f6fcce284bc690302ddcfc8283aeaefc1b08aeeaf12fa28"

def generate_content_sign(payload: dict, token: str, timestamp: str) -> str:
    payload_str = json.dumps(payload, separators=(',', ':'))
    full_md5 = hashlib.md5((token + timestamp).encode('utf-8')).hexdigest()
    sliced_md5 = full_md5[7:]
    content_sign = hashlib.md5((timestamp + payload_str + sliced_md5).encode('utf-8')).hexdigest()
    return content_sign, payload_str

def open_trade(side):
    payload = {
        "symbol": symbol,
        "side": side,  # 1 = long, 3 = short
        "openType": 1,
        "type": "5",
        "vol": 2,
        "leverage": 2,
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
    if len(sys.argv) < 2:
        print("Usage: python open_trade.py [1=long | 3=short]")
        sys.exit(1)

    side_arg = int(sys.argv[1])
    if side_arg not in [1, 3]:
        print("Side must be 1 (long) or 3 (short)")
        sys.exit(1)

    open_trade(side_arg)
