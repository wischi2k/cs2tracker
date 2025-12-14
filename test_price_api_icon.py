import requests
import json

# Try the Price Overview API
hash_name = 'M4A4 | Neo-Noir (Minimal Wear)'
url = f'https://steamcommunity.com/market/priceoverview/?appid=730&market_hash_name={hash_name.replace(" ", "%20")}'
try:
    r = requests.get(url, timeout=12)
    data = r.json()
    print('Keys:', list(data.keys()))
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error: {e}')
