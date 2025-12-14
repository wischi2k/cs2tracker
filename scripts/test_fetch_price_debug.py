#!/usr/bin/env python3
# Debug the full fetch_price_cents_overview function
from __future__ import annotations
import json, re
from typing import Optional
import urllib.parse as up
import requests

def parse_eur_to_cents(s: str) -> Optional[int]:
    if not s:
        return None
    s = s.replace("\u00a0", "")  # NBSP
    s = s.replace("€", "").replace("EUR", "").strip()
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return int(round(float(s) * 100))
    except ValueError:
        return None

def get_json_bom_safe(url: str, timeout: int = 15) -> Optional[dict]:
    try:
        r = requests.get(url, timeout=timeout)
        txt = r.text.lstrip("\ufeff")
        return json.loads(txt)
    except Exception as e:
        print(f"get_json_bom_safe error: {e}")
        return None

def fetch_price_cents_overview(market_hash: str) -> Optional[int]:
    url = ("https://steamcommunity.com/market/priceoverview/"
           f"?appid=730&currency=3&market_hash_name={up.quote(market_hash)}")
    print(f"URL: {url}")
    j = get_json_bom_safe(url)
    print(f"JSON: {j}")
    if not j or not j.get("success"):
        print(f"No success or no JSON")
        return None
    price_str = j.get("lowest_price") or j.get("median_price") or ""
    print(f"price_str: '{price_str}'")
    cents = parse_eur_to_cents(price_str)
    print(f"cents: {cents}")
    return cents

# Test
mh = "M4A4 | Neo-Noir (Minimal Wear)"
result = fetch_price_cents_overview(mh)
print(f"\nFinal result: {result}")
