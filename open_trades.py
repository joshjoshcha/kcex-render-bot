import os
import hashlib
import time
import requests
import json
import sys
from datetime import datetime

# === CONFIG ===
token = "WEB663befad1836c776248784de5fcfa5ff76c2869004531a0f74370f6066e54b5d"

volume_multipliers = {
    "BONK_USDT": 100000,
    "SHIB_USDT": 100000,
    "DOGE_USDT": 10,
    "TON_USDT": 1,
    "POPCAT_USDT": 10
}

def generate_content_sign(payload: dict, token: str, timestamp: str):
    payload_str = json.dumps(payload, separators=(',', ':'))
    full_md5 = hashlib.md5((token + timestamp).encode()).hexdigest()
    sliced = full_md5[7:]
    content_sign = hashlib.md5((timestamp + payload_str + sliced).encode()).hexdigest()
    return content_sign, payload_str

def get_recent_trade_price(symbol):
    now = int(time.time() * 1000)
    start = now - 5 * 24 * 60 * 60 * 1000  # last 5 days

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
        print(
            f"[BALANCE] HTTP {res.status_code} | "
            f"type={res.headers.get('Content-Type', 'missing')} | "
            f"bytes={len(res.content)} | redirects={len(res.history)}",
            flush=True,
        )
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
    leverage = 5

    payload = {
        "symbol": symbol,
        "side": side,
        "openType": 1,
        "type": "5",
        "vol": 4,
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


