#!/usr/bin/env python3
# Test fetch_meta_from_listing für M4A4 Neo-Noir
import requests
from bs4 import BeautifulSoup
import re, html
from urllib.parse import quote

market_hash = "M4A4 | Neo-Noir (Minimal Wear)"
url = f"https://steamcommunity.com/market/listings/730/{quote(market_hash)}?l=german"
print(f"URL: {url}\n")

try:
    html_text = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html_text, "html.parser")
    
    name_el = soup.select_one("#largeiteminfo_item_name")
    type_el = soup.select_one("#largeiteminfo_item_type")
    icon_el = soup.select_one("#largeiteminfo_item_icon img")
    
    print(f"name_el found: {name_el is not None}")
    if name_el:
        print(f"  text: {name_el.get_text(strip=True)}")
    
    print(f"type_el found: {type_el is not None}")
    if type_el:
        print(f"  text: {type_el.get_text(strip=True)}")
    
    print(f"icon_el found: {icon_el is not None}")
    if icon_el:
        print(f"  src: {icon_el.get('src')}")
    
    # Test extraction
    display_name = name_el.get_text(strip=True) if name_el else market_hash
    item_type = type_el.get_text(strip=True) if type_el else ""
    
    if not icon_el:
        m = re.search(r'https://steamcommunity-a\.akamaihd\.net/economy/image/[^"]+', html_text)
        icon_src = html.unescape(m.group(0)) if m else None
    else:
        icon_src = icon_el.get("src")
    
    print(f"\nERGEBNIS:")
    print(f"  display_name: {display_name}")
    print(f"  item_type: {item_type}")
    print(f"  icon_src: {'[EXISTS]' if icon_src else '[NONE]'}")
    
except Exception as e:
    print(f"ERROR: {e}")
