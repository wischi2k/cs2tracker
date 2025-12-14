# fetch_all.py
from __future__ import annotations
import argparse, json, re, time
import sqlite3
from typing import Optional, Tuple
import urllib.parse as up

import requests

DB_PATH = "cs2_prices.sqlite"

# ---------- HTTP helpers ----------

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
SESS = requests.Session()
SESS.headers.update({"User-Agent": UA})

def get_json_bom_safe(url: str, timeout: int = 15) -> Optional[dict]:
    try:
        r = SESS.get(url, timeout=timeout)
        txt = r.text.lstrip("\ufeff")
        return json.loads(txt)
    except Exception:
        return None

# ---------- price parsing ----------

def parse_eur_to_cents(s: str) -> Optional[int]:
    """
    '2,35€' | '1.234,56 €' | '€ 0,92' | '84,--€' -> 235 | 123456 | 92 | 8400
    """
    if not s:
        return None
    s = s.replace("\u00a0", "")  # NBSP
    s = s.replace("€", "").replace("EUR", "").strip()
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s:
        return None
    # Ersetze '--' mit '00' (z.B. '84,--' -> '84,00')
    s = s.replace("--", "00")
    # Entferne alle verbleibenden Minus-Zeichen (negativ-Flag)
    is_negative = s.startswith("-")
    s = s.lstrip("-")
    if "," in s:  # EU-Format
        s = s.replace(".", "").replace(",", ".")
    try:
        val = float(s)
        if is_negative:
            val = -val
        return int(round(val * 100))
    except ValueError:
        return None

def fetch_price_cents_overview(market_hash: str) -> Optional[int]:
    url = ("https://steamcommunity.com/market/priceoverview/"
           f"?appid=730&currency=3&market_hash_name={up.quote(market_hash)}")
    j = get_json_bom_safe(url)
    if not j or not j.get("success"):
        return None
    price_str = j.get("lowest_price") or j.get("median_price") or ""
    return parse_eur_to_cents(price_str)

def find_best_name_via_search(query: str) -> Optional[str]:
    """
    Nutzt search/render, um den korrekten Namen zu finden.
    Validiert, dass der Treffer exakt dem Query entspricht (verhindert falsche Treffer).
    """
    url = (f"https://steamcommunity.com/market/search/render/"
           f"?appid=730&norender=1&count=1&query={up.quote(query)}")
    j = get_json_bom_safe(url)
    if not j or not j.get("success"):
        return None
    res = (j.get("results") or [])
    if not res:
        return None
    r0 = res[0]
    # Validierung: nur akzeptieren wenn Treffer exakt dem Query entspricht
    result_name = r0.get("name") or r0.get("hash_name")
    if result_name and result_name.strip() == query.strip():
        return result_name
    # Wenn kein exakter Treffer, nicht fallback zu falschem Treffer
    return None

def fetch_price_cents_robust(market_hash: str) -> Tuple[Optional[int], str]:
    """
    1) priceoverview(market_hash)
    2) wenn None: search/render(query=market_hash) -> name -> priceoverview(name)
    Rückgabe: (cents, verwendeter_name)
    """
    p = fetch_price_cents_overview(market_hash)
    if p is not None:
        return p, market_hash
    best = find_best_name_via_search(market_hash)
    if best:
        p2 = fetch_price_cents_overview(best)
        return p2, best
    return None, market_hash

# ---------- DB helpers ----------

def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def ensure_prices_table(con: sqlite3.Connection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            item_id INTEGER NOT NULL,
            ts INTEGER NOT NULL,
            price_cents INTEGER NOT NULL
        )
    """)
    con.commit()

def items_to_fetch(con: sqlite3.Connection, only_missing: bool) -> list[sqlite3.Row]:
    if only_missing:
        sql = """
        SELECT i.id, i.market_hash, i.display_name
        FROM items i
        LEFT JOIN prices p ON p.item_id = i.id
        GROUP BY i.id
        HAVING COUNT(p.rowid)=0
        ORDER BY i.id
        """
        return con.execute(sql).fetchall()
    else:
        sql = """
        SELECT i.id, i.market_hash, i.display_name
        FROM items i
        WHERE IFNULL(i.is_active,1)=1
        ORDER BY i.id
        """
        return con.execute(sql).fetchall()

def insert_snapshot(con: sqlite3.Connection, item_id: int, cents: int) -> None:
    con.execute("INSERT INTO prices(item_id, ts, price_cents) VALUES(?,?,?)",
                (item_id, int(time.time()), int(cents)))
    con.commit()

# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="Fetch CS2 prices for items")
    ap.add_argument("--only-missing", action="store_true",
                    help="Nur Items ohne irgendeinen Preis-Snapshot holen")
    ap.add_argument("--sleep", type=float, default=1.0,
                    help="Sekunden zwischen Requests (Default: 1.0)")
    args = ap.parse_args()

    con = connect()
    ensure_prices_table(con)
    rows = items_to_fetch(con, args.only_missing)

    if not rows:
        print("Nichts zu tun.")
        return

    print(f"{len(rows)} Items werden aktualisiert "
          f"({'nur fehlende' if args.only_missing else 'alle aktiven'}).")

    for r in rows:
        item_id = r["id"]
        mh = (r["market_hash"] or "").strip()
        name = r["display_name"]
        if not mh:
            print(f"[{item_id}] SKIP: Kein market_hash (Name: {name})")
            continue

        cents, used_name = fetch_price_cents_robust(mh)
        if cents is None:
            print(f"[{item_id}] FEHLER: Kein Preis gefunden für '{mh}' "
                  f"(evtl. korrigierter Name via Suche: {used_name!r})")
        else:
            insert_snapshot(con, item_id, cents)
            eur = cents / 100.0
            suffix = "" if used_name == mh else f" (via Suche: {used_name})"
            print(f"[{item_id}] OK: {eur:.2f} €{suffix}")

        time.sleep(max(0.0, args.sleep))

    con.close()

if __name__ == "__main__":
    main()
