#!/usr/bin/env python3
# Test search/render API directly
import requests
import json
from urllib.parse import quote

market_hash = "M4A4 | Neo-Noir (Minimal Wear)"
url = f"https://steamcommunity.com/market/search/render/?appid=730&norender=1&count=1&query={quote(market_hash)}"
print(f"URL: {url}\n")

try:
    resp = requests.get(url, timeout=10)
    j = resp.json()
    print(f"success: {j.get('success')}")
    if j.get("success") and j.get("results"):
        r0 = j["results"][0]
        name = r0.get("name") or market_hash
        hash_name = r0.get("hash_name")
        print(f"name: {name}")
        print(f"hash_name: {hash_name}")
        print(f"match: {name == market_hash}")
        
        desc = r0.get("asset_description") or {}
        typ = desc.get("type", "")
        icon_path = desc.get("icon_url")
        print(f"type: {typ}")
        print(f"icon_path: {icon_path[:50] if icon_path else None}...")
        
        # Check if result matches the query
        if name != market_hash and hash_name != market_hash:
            print(f"\n⚠️ MISMATCH: Query '{market_hash}' != Result '{name}'")
except Exception as e:
    print(f"ERROR: {e}")
