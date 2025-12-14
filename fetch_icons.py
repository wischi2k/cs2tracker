# fetch_icons.py
import sqlite3, urllib.parse as up, requests, re, html

def steam_icon(hash_name: str) -> str | None:
    """
    Holt das Item-Thumbnail über die offizielle Search-API und baut die finale URL.
    Validiert, dass der Treffer exakt dem hash_name entspricht (verhindert falsche Icons).
    Fallback: Versucht HTML-Parsing wenn Search-API fehlschlägt.
    """
    # 1) Versuche Search-API mit Validierung (zuerst enger, dann breiter)
    q = up.quote(hash_name)
    try:
        # enge Suche (schnell)
        url = f"https://steamcommunity.com/market/search/render/?appid=730&norender=1&count=1&query={q}"
        j = requests.get(url, timeout=12).json()
        if j.get("success"):
            results = j.get("results") or []
            if results:
                result_name = results[0].get("name") or results[0].get("hash_name")
                if result_name and result_name.strip() == hash_name.strip():
                    path = results[0].get("asset_description", {}).get("icon_url")
                    if path:
                        return f"https://steamcommunity-a.akamaihd.net/economy/image/{path}"

        # breitere Suche: mehr Treffer durchgehen und nach exaktem market_hash_name prüfen
        url2 = f"https://steamcommunity.com/market/search/render/?appid=730&norender=1&count=100&query={q}"
        j2 = requests.get(url2, timeout=12).json()
        if j2.get("success"):
            results2 = j2.get("results") or []
            for res in results2:
                asset = res.get("asset_description") or {}
                mhash = asset.get("market_hash_name") or res.get("hash_name") or res.get("name")
                if mhash and mhash.strip() == hash_name.strip():
                    path = asset.get("icon_url")
                    if path:
                        return f"https://steamcommunity-a.akamaihd.net/economy/image/{path}"

            # Letzte Rettung: kein exakter Treffer gefunden, aber wenn erstes Ergebnis ein Icon hat,
            # nutzen wir das als Fallback (besser ein Icon als keins). WARNUNG wird zurückgegeben.
            if results2:
                first_asset = results2[0].get("asset_description") or {}
                path = first_asset.get("icon_url")
                if path:
                    # markiere als unvalidated fallback (keine Änderung an DB-API; main() loggt Warnung)
                    return (f"FALLBACK::https://steamcommunity-a.akamaihd.net/economy/image/{path}")
    except Exception:
        pass
    
    # 2) Fallback: Versuche HTML-Parsing von der Listing-Seite
    try:
        page = requests.get(f"https://steamcommunity.com/market/listings/730/{up.quote(hash_name)}", timeout=12).text
        m_img = re.search(r'https://steamcommunity-a\.akamaihd\.net/economy/image/[^"\']+', page)
        if m_img:
            return html.unescape(m_img.group(0))
    except Exception:
        pass
    
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
            # handle FALLBACK:: marker: store cleaned URL and warn
            if isinstance(icon, str) and icon.startswith("FALLBACK::"):
                real = icon.split("FALLBACK::", 1)[1]
                con.execute("UPDATE items SET icon_url=? WHERE id=?", (real, r["id"]))
                print(f"⚠️ Fallback-Icon (unvalidated) gesetzt: {r['market_hash']}")
            else:
                con.execute("UPDATE items SET icon_url=? WHERE id=?", (icon, r["id"]))
                print(f"✔ Icon gesetzt: {r['market_hash']}")
        else:
            print(f"✖ Kein Icon gefunden: {r['market_hash']}")
    con.commit()
    con.close()

if __name__ == "__main__":
    main()
