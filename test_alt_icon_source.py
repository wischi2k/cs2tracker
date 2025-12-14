import sqlite3

DB = 'cs2_prices.sqlite'
con = sqlite3.connect(DB)

# Get the M4A4 Neo-Noir item ID
row = con.execute("SELECT id FROM items WHERE market_hash LIKE '%Neo-Noir%'").fetchone()
if row:
    item_id = row[0]
    # Fetch from the search/render API using a working icon URL from a known good result
    # Alternative: Set a placeholder icon and let user manually set it
    # For now, let's try fetching from another source
    
    # Query Valve's CDN directly with a made-up icon hash (this won't work, but shows the pattern)
    # Better: Just try the Steam inventory helper or accept that some items can't be auto-fetched
    
    # Actually, let's try querying the Steam Community Inventory helper
    # It returns JSON with icon URLs
    
    import requests
    import json
    
    url = f"https://steamcommunity.com/inventory/render/?appid=730&market_hash_name=M4A4%20%7C%20Neo-Noir%20%28Minimal%20Wear%29"
    try:
        r = requests.get(url, timeout=12)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Data keys: {data.keys()}")
    except Exception as e:
        print(f"Error: {e}")

con.close()
