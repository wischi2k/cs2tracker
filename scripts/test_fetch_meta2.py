#!/usr/bin/env python3
# Test alternative: parse JSON from page
import requests
import re, json
from urllib.parse import quote

market_hash = "M4A4 | Neo-Noir (Minimal Wear)"
url = f"https://steamcommunity.com/market/listings/730/{quote(market_hash)}?l=german"
print(f"URL: {url}\n")

try:
    html_text = requests.get(url, timeout=15).text
    
    # Try: extract window.history.replaceState data or similar
    # Look for gApp data
    m = re.search(r'"name"\s*:\s*"([^"]+)"', html_text)
    if m:
        print(f"Name via regex: {m.group(1)}")
    
    # Look for type
    m_type = re.search(r'"type"\s*:\s*"([^"]+)"', html_text)
    if m_type:
        print(f"Type via regex: {m_type.group(1)}")
    
    # Look for image icon
    m_img = re.search(r'https://steamcommunity-a\.akamaihd\.net/economy/image/[^"']+', html_text)
    if m_img:
        print(f"Icon via regex: {m_img.group(0)[:80]}...")
    
    # Also check the page title
    m_title = re.search(r'<title>(.*?)</title>', html_text, re.IGNORECASE)
    if m_title:
        print(f"Title: {m_title.group(1)}")
    
except Exception as e:
    print(f"ERROR: {e}")
