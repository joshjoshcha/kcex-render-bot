import hashlib
import time
import requests
import json
import sys
from datetime import datetime

# === CONFIG ===
token = "WEBeb44bcf35c5d87703043fa532dbe31f32acee8758dc0064976bb22aae4ba3438"

# Symbol-specific volume multipliers (used to convert USDT to position size)
volume_multipliers = {
    "BONK_USDT": 100000,
    "GROK_USDT": 1,
    "PENGU_USDT": 1000,
}

# Symbol-specific base target USDT (assumes this is correct for 50 USDT balance)
base_targets = {
    "BONK_USDT": 100,
    "GROK_USDT": 25,
    "PENGU_USDT": 50,
}

def generate_content_sign(payload: dict, token: str, timestamp: str):
    payload_str = json.dumps(payload, separators=(',', ':'))
    full_md5 = hashlib.md5((token + timestamp).encode()).hexdigest()
    sliced = full_md5[7:]
    content_sign = hashlib.md5((timestamp + payload_str + sliced).encode()).hexdigest()
    return content_sign, payload_str

def get_recent_trade_price(symbol):
    now = int(time.time() * 1000)
    start = now - 3 * 24 * 60 * 60 * 1000  # last 3 days

    params = {
        "category": 1,
        "symbol": symbol,
        "states": 3,  # filled
        "page_num": 1,
        "page_size": 200,
        "start_time": start,
        "end_time": now
    }

    headers = {"Authorization": token}
    url = "https://www.kcex.com/fapi/v1/private/order/list/history_orders"
    res = requests.get(url, headers=headers, params=params)
    data = res.json().get("data", [])

    for trade in sorted(data, key=lambda o: o.get("ts", o.get("createTime", 0)), reverse=True):
        if "dealAvgPrice" in trade and float(trade["dealAvgPrice"]) > 0:
            trade_time_ms = trade.get("ts") or trade.get("createTime")
            trade_time_str = datetime.utcfromtimestamp(trade_time_ms / 1000).strftime("%Y-%m-%d %H:%M:%S GMT")
            return float(trade["dealAvgPrice"]), trade_time_str

    raise Exception("No recent filled trades found with a valid price.")

def fetch_total_asset_overview():
    url = "https://www.kcex.com/api/platform/asset/api/asset_analysis/total/overview"
    timestamp = str(int(time.time() * 1000))
    full_md5 = hashlib.md5((token + timestamp).encode()).hexdigest()
    sliced = full_md5[7:]
    content_sign = hashlib.md5((timestamp + "" + sliced).encode()).hexdigest()

    headers = {
        "Authorization": token,
        "Content-time": timestamp,
        "Content-sign": content_sign,
        "Content-Type": "application/json"
    }

    try:
        res = requests.get(url, headers=headers)
        data = res.json()

        if data.get("code") != 0:
            print("[ERROR] Could not fetch asset overview:", data)
            return 0.0

        asset_data = data.get("data", {})
        total_asset = asset_data.get("totalAsset", "N/A")
        spot_asset = asset_data.get("spotAsset", "N/A")
        contract_asset = asset_data.get("contractAsset", "0")

        ts = data.get("timestamp")
        if ts:
            ts_formatted = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S GMT")
        else:
            ts_formatted = "Unknown time"

        print(f"[{ts_formatted}] Total Asset: {total_asset} USDT (Spot: {spot_asset}, Contract: {contract_asset})")
        return float(contract_asset)

    except Exception as e:
        print("[ERROR] Balance request failed:", e)
        return 0.0

def open_trade(side, symbol):
    contract_balance = fetch_total_asset_overview()
    if contract_balance <= 0:
        print("[ERROR] No contract balance available. Aborting.")
        return

    volume_multiplier = volume_multipliers.get(symbol)
    base_target_usdt = base_targets.get(symbol)

    if volume_multiplier is None or base_target_usdt is None:
        print(f"[ERROR] Missing volume multiplier or base target for {symbol}.")
        return

    scaled_target_usdt = base_target_usdt * (contract_balance / 50)

    price, price_time = get_recent_trade_price(symbol)
    vol = int(scaled_target_usdt / (price * volume_multiplier))
    leverage = 4  # ← Random value; adjust per symbol later if needed

    print(f"[INFO] Using recent deal price {price} from {price_time}")
    print(f"[INFO] Adjusted target USDT: {scaled_target_usdt:.2f}, computed volume = {vol}")
    print(f"[INFO] Leverage (hardcoded): {leverage}")

    payload = {
        "symbol": symbol,
        "side": side,
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
    print("Response:", json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python open_trades.py [side: 1=long,3=short] [symbol]")
        sys.exit(1)

    side = int(sys.argv[1])
    symbol = sys.argv[2].upper()

    open_trade(side, symbol)


