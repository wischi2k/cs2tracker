import requests, re, html
from urllib.parse import quote

mh = "M4A4 | Neo-Noir (Minimal Wear)"
url = f"https://steamcommunity.com/market/listings/730/{quote(mh)}"
print(f"Testing: {url}\n")

try:
    page = requests.get(url, timeout=12).text
    print(f"Page length: {len(page)}")
    
    # Suche nach Icons
    matches = re.findall(r'https://steamcommunity-a\.akamaihd\.net/economy/image/[^"']+', page)
    if matches:
        print(f"Found {len(matches)} icon URLs")
        for i, m in enumerate(matches[:3]):
            print(f"  {i}: {m[:100]}...")
    else:
        print("No icons found in HTML")
    
    # Check if page is loaded by JS
    if "gApp" in page or "window.__initial" in page:
        print("\nPage seems to be JavaScript-rendered (API data embedded)")
    if "<title>" in page:
        m = re.search(r'<title>(.*?)</title>', page)
        print(f"Title: {m.group(1) if m else 'N/A'}")
        
except Exception as e:
    print(f"ERROR: {e}")
