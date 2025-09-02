import hashlib
import time
import requests
import json
import sys

# === CONFIG ===
token = "WEB1bb9ed9660886642d82218e3c2c813b5e483329ea13df272eb42543365ea61a0"

def generate_content_sign(payload: dict, token: str, timestamp: str):
    payload_str = json.dumps(payload, separators=(',', ':'))
    full_md5 = hashlib.md5((token + timestamp).encode()).hexdigest()
    sliced = full_md5[7:]
    content_sign = hashlib.md5((timestamp + payload_str + sliced).encode()).hexdigest()
    return content_sign, payload_str

def get_position_id(target_side, symbol):
    now = int(time.time() * 1000)
    start = now - 3 * 24 * 60 * 60 * 1000

    params = {
        "category": 1,
        "symbol": symbol,
        "states": 3,
        "start_time": start,
        "end_time": now,
        "page_num": 1,
        "page_size": 400
    }

    headers = {"Authorization": token}
    url = "https://www.kcex.com/fapi/v1/private/order/list/history_orders"
    res = requests.get(url, headers=headers, params=params)
    data = res.json().get("data", [])

    valid = [o for o in data if o["side"] == target_side and o["symbol"] == symbol and o["state"] == 3]
    if not valid:
        raise Exception("No active position found for side: " + str(target_side))

    latest = sorted(valid, key=lambda o: o.get("ts", o.get("createTime", 0)), reverse=True)[0]
    return latest["positionId"], latest["vol"], latest["leverage"]

def close_trade(entry_side, symbol):
    close_side = 4 if entry_side == 1 else 2  # 4 = close long, 2 = close short
    position_id, vol, leverage = get_position_id(entry_side, symbol)

    payload = {
        "symbol": symbol,
        "openType": 1,
        "positionId": position_id,
        "leverage": leverage,
        "type": 5,
        "vol": vol,
        "side": close_side,
        "flashClose": True,
        "priceProtect": "0"
    }

    timestamp = str(int(time.time() * 1000))
    sign, payload_str = generate_content_sign(payload, token, timestamp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
        "Content-time": timestamp,
        "Content-sign": sign,
        "Accept": "*/*"
    }

    url = "https://www.kcex.com/fapi/v1/private/order/create"
    res = requests.post(url, headers=headers, data=payload_str)

    print("Close Response:", res.status_code)
    print(res.text)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python close_trade.py [1=long | 3=short] [symbol]")
        sys.exit(1)

    entry_side = int(sys.argv[1])
    symbol = sys.argv[2]

    if entry_side not in [1, 3]:
        print("Side must be 1 (long) or 3 (short)")
        sys.exit(1)

    close_trade(entry_side, symbol)
