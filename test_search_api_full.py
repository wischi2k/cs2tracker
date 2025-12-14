import requests
import json
import urllib.parse as up

# Check what the Search API actually returns for Neo-Noir
hash_name = 'M4A4 | Neo-Noir (Minimal Wear)'
q = up.quote(hash_name)
url = f"https://steamcommunity.com/market/search/render/?appid=730&norender=1&count=1&query={q}"

try:
    response = requests.get(url, timeout=12)
    data = response.json()
    print("Success:", data.get("success"))
    results = data.get("results") or []
    if results:
        result = results[0]
        print("\nFirst result:")
        print("  name:", result.get("name"))
        print("  hash_name:", result.get("hash_name"))
        
        asset_desc = result.get("asset_description") or {}
        print("\nAsset description keys:", list(asset_desc.keys()))
        print("  icon_url:", asset_desc.get("icon_url"))
        print("  icon_url_large:", asset_desc.get("icon_url_large"))
        
        # Print first few keys from asset_description
        for key in list(asset_desc.keys())[:10]:
            val = asset_desc[key]
            if isinstance(val, str) and len(val) < 100:
                print(f"  {key}: {val}")
except Exception as e:
    print(f"Error: {e}")
