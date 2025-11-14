# fetch_icons.py
import sqlite3, urllib.parse as up, requests

def steam_icon(hash_name: str) -> str | None:
    """
    Holt das Item-Thumbnail über die offizielle Search-API und baut die finale URL.
    """
    q = up.quote(hash_name)
    url = f"https://steamcommunity.com/market/search/render/?appid=730&norender=1&count=1&query={q}"
    try:
        j = requests.get(url, timeout=12).json()
        if not j.get("success"):
            return None
        results = j.get("results") or []
        if not results:
            return None
        path = results[0].get("asset_description", {}).get("icon_url")
        if not path:
            return None
        return f"https://steamcommunity-a.akamaihd.net/economy/image/{path}"
    except Exception:
        return None

def main():
    con = sqlite3.connect("cs2_prices.sqlite")
    con.row_factory = sqlite3.Row

    rows = con.execute("""
        SELECT id, market_hash
        FROM items
        WHERE (icon_url IS NULL OR icon_url='') AND IFNULL(is_active,1)=1
    """).fetchall()

    if not rows:
        print("ℹ️ Keine offenen Items ohne Icon gefunden.")
    for r in rows:
        icon = steam_icon(r["market_hash"])
        if icon:
            con.execute("UPDATE items SET icon_url=? WHERE id=?", (icon, r["id"]))
            print(f"✔ Icon gesetzt: {r['market_hash']}")
        else:
            print(f"✖ Kein Icon gefunden: {r['market_hash']}")
    con.commit()
    con.close()

if __name__ == "__main__":
    main()
