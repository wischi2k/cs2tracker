#!/usr/bin/env python3
import requests
from urllib.parse import quote

# Test priceoverview with the exact hash
mh = "M4A4 | Neo-Noir (Minimal Wear)"
url = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency=3&market_hash_name={quote(mh)}"
print(f"Testing: {url}\n")

try:
    r = requests.get(url, timeout=15)
    j = r.json()
    print(f"Response: {j}")
    if j.get("success"):
        print(f"✓ Price found: {j.get('lowest_price')}")
    else:
        print(f"✗ No price data (item may not exist on market or hash is wrong)")
except Exception as e:
    print(f"ERROR: {e}")
