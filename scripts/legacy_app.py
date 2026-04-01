from __future__ import annotations
import os
import re, html, json, time
import sqlite3
from typing import Any, Optional
from urllib.parse import urlparse, unquote, quote
import urllib.parse as up

import requests
from bs4 import BeautifulSoup
from flask import (
    Flask, render_template, request, redirect, url_for, jsonify, flash
)
from telegram_util import tg_send

DB_PATH = "cs2_prices.sqlite"
FEE_RATE = 0.15  # fixer Steam-Satz

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cs2tracker_dev_secret_change_me")

# ---------------------------- DB Utils ----------------------------

def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 30000")
    return con

def has_column(con: sqlite3.Connection, table: str, col: str) -> bool:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == col for r in rows)

def ensure_schema() -> None:
    con = connect()
    try:
        # optionale Spalten
        if not has_column(con, "items", "icon_url"):
            con.execute("ALTER TABLE items ADD COLUMN icon_url TEXT")
        if not has_column(con, "items", "category"):
            con.execute("ALTER TABLE items ADD COLUMN category TEXT")
        if not has_column(con, "items", "is_active"):
            con.execute("ALTER TABLE items ADD COLUMN is_active INTEGER DEFAULT 1")
        # Preise (falls noch nicht vorhanden)
        con.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                item_id INTEGER NOT NULL,
                ts      INTEGER NOT NULL,
                price_cents INTEGER NOT NULL
            )
        """)
        # Alerts
        con.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
              item_id INTEGER PRIMARY KEY,
              threshold_net_eur REAL,
              above_threshold INTEGER DEFAULT 0
            )
        """)
        con.commit()
    finally:
        con.close()

ensure_schema()

# ---------------------- Preis-Fetch & Helpers ---------------------

def eur(cents: Optional[int]) -> Optional[float]:
    return None if cents is None else cents / 100.0

def _parse_eur_to_cents(s: str) -> Optional[int]:
    """
    Wandelt Preisstrings wie '2,35€', '1.234,56 €', '€ 0,92' robust in Cents um.
    """
    if not s:
        return None
    s = s.replace("\u00a0", "")  # NBSP
    s = s.replace("€", "").replace("EUR", "").strip()
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s:
        return None
    if "," in s:  # EU-Format
        s = s.replace(".", "").replace(",", ".")
    try:
        val = float(s)
        return int(round(val * 100))
    except ValueError:
        return None

def fetch_price_cents(market_hash: str) -> Optional[int]:
    """
    Holt 'lowest_price' (EUR) aus priceoverview; currency=3 -> EUR.
    """
    url = ("https://steamcommunity.com/market/priceoverview/"
           f"?appid=730&currency=3&market_hash_name={up.quote(market_hash)}")
    try:
        resp = requests.get(url, timeout=15)
        txt = resp.text.lstrip("\ufeff")  # evtl. UTF-8 BOM
        data = json.loads(txt)
        if not data.get("success"):
            return None
        price_str = data.get("lowest_price") or data.get("median_price") or ""
        return _parse_eur_to_cents(price_str)
    except Exception:
        return None

def insert_price_snapshot(item_id: int, price_cents: int) -> None:
    con = connect()
    try:
        con.execute(
            "INSERT INTO prices(item_id, ts, price_cents) VALUES(?,?,?)",
            (item_id, int(time.time()), int(price_cents))
        )
        con.commit()
    finally:
        con.close()

def current_price_cents(con: sqlite3.Connection, item_id: int) -> Optional[int]:
    row = con.execute(
        "SELECT price_cents FROM prices WHERE item_id=? ORDER BY ts DESC LIMIT 1",
        (item_id,)
    ).fetchone()
    return None if not row else int(row[0])

def item_row_to_dict(con: sqlite3.Connection, r: sqlite3.Row) -> dict[str, Any]:
    buy_c = r["buy_price_cents"]
    cur_c = current_price_cents(con, r["id"])
    net_c = None if cur_c is None else int(round(cur_c * (1 - FEE_RATE)))
    active_val = 1 if ("is_active" not in r.keys() or r["is_active"] is None) else int(r["is_active"])
    return {
        "id":     r["id"],
        "name":   r["display_name"],
        "icon":   r["icon_url"],
        "cat":    r["category"] if "category" in r.keys() else None,
        "active": active_val,
        "buy":    eur(buy_c),
        "cur":    eur(cur_c),
        "net":    eur(net_c),
        "diff_g": None if None in (buy_c, cur_c) else eur(cur_c - buy_c),
        "diff_n": None if None in (buy_c, cur_c) else eur(net_c - buy_c),
    }

def build_chart_payload(con: sqlite3.Connection, item_id: int, buy_eur: Optional[float]) -> dict[str, Any]:
    rows = con.execute(
        "SELECT ts, price_cents FROM prices WHERE item_id=? ORDER BY ts ASC",
        (item_id,)
    ).fetchall()
    ts = [int(r["ts"]) for r in rows]
    lowest = [eur(r["price_cents"]) for r in rows]
    return {"ts": ts, "lowest": lowest, "buy": buy_eur}

# --------------------- Steam-Scrape / Normalisierung -------------

STEAM_HOST = "steamcommunity.com"

def parse_input_to_hash(s: str) -> str:
    """
    Akzeptiert Steam-URL ODER bereits den Market-Hash; liefert den Hash.
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("Leere Eingabe.")
    if s.startswith("http"):
        u = urlparse(s)
        if STEAM_HOST not in u.netloc:
            raise ValueError("Keine gültige Steam-URL.")
        parts = [p for p in u.path.split("/") if p]
        try:
            idx = parts.index("listings")
            hash_part = parts[idx + 2]
        except Exception:
            raise ValueError("URL-Format unerwartet. Erwartet: /market/listings/730/<name>")
        return unquote(hash_part)
    return s

def normalize_category(type_txt: str) -> str:
    t = (type_txt or "").lower()
    if any(k in t for k in ["behälter", "kiste", "case", "container"]):
        return "Kiste"
    if "sticker" in t or "aufkleber" in t:
        return "Sticker"
    if "handschuh" in t:
        return "Handschuhe"
    if "agent" in t:
        return "Agent"
    if "messer" in t:
        return "Messer"
    if "graffiti" in t:
        return "Graffiti"
    if "musik" in t:
        return "Musik-Kit"
    if "patch" in t:
        return "Patch"
    if any(k in t for k in ["gewehr", "pistole", "smg", "maschinenpistole", "schrotflinte", "scharfschütze", "heavy"]):
        return "Waffen-Skin"
    return "Unbekannt"

def fetch_meta_from_listing(market_hash: str) -> dict[str, Optional[str]]:
    url = f"https://steamcommunity.com/market/listings/730/{quote(market_hash)}?l=german"
    html_text = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html_text, "html.parser")
    name_el = soup.select_one("#largeiteminfo_item_name")
    type_el = soup.select_one("#largeiteminfo_item_type")
    icon_el = soup.select_one("#largeiteminfo_item_icon img")
    if not icon_el:
        m = re.search(r'https://steamcommunity-a\.akamaihd\.net/economy/image/[^"]+', html_text)
        icon_src = html.unescape(m.group(0)) if m else None
    else:
        icon_src = icon_el.get("src")
    display_name = name_el.get_text(strip=True) if name_el else market_hash
    item_type = type_el.get_text(strip=True) if type_el else ""
    category = normalize_category(item_type)
    return {"display_name": display_name, "category": category, "icon_url": icon_src}

def _parse_market_hash_from_url(steam_url: str) -> str | None:
    m = re.search(r"/market/listings/730/([^/?#]+)", steam_url)
    return up.unquote(m.group(1)) if m else None

def _fetch_meta_for_hash(mh: str) -> tuple[str, str | None, str | None]:
    # 1) schnelle JSON-Suche — validiert exakte Treffer
    url = (f"https://steamcommunity.com/market/search/render/?"
           f"appid=730&norender=1&count=1&query={up.quote(mh)}")
    try:
        j = requests.get(url, timeout=10).json()
        if j.get("success") and j.get("results"):
            r0 = j["results"][0]
            result_name = r0.get("name") or r0.get("hash_name") or ""
            # Validierung: nur akzeptieren wenn Treffer exakt dem Query entspricht
            if result_name and result_name.strip() == mh.strip():
                name = result_name
                desc = r0.get("asset_description") or {}
                icon_path = desc.get("icon_url")
                icon = f"https://steamcommunity-a.akamaihd.net/economy/image/{icon_path}" if icon_path else None
                typ = (desc.get("type") or "").lower()
                if "case" in typ or "container" in typ:
                    cat = "Kiste"
                elif "sticker" in typ:
                    cat = "Sticker"
                elif "agent" in typ:
                    cat = "Agent"
                elif "key" in typ:
                    cat = "Schlüssel"
                elif "patch" in typ:
                    cat = "Patch"
                elif "music" in typ:
                    cat = "Musik-Kit"
                else:
                    cat = "Waffen-Skin"
                return (name, icon, cat)
    except Exception:
        pass
    # 2) Fallback HTML
    try:
        page = requests.get(f"https://steamcommunity.com/market/listings/730/{up.quote(mh)}", timeout=10).text
        m_title = re.search(r"<title>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
        title = html.unescape(m_title.group(1)).strip() if m_title else mh
        if " - Steam Community Market" in title:
            name = title.replace(" - Steam Community Market", "")
            name = re.sub(r"^\s*Counter-Strike\s*[\d]?\s*-\s*", "", name).strip()
        else:
            name = mh
        m_img = re.search(r'https://steamcommunity-a\.akamaihd\.net/economy/image/[^"]+', page)
        icon = html.unescape(m_img.group(0)) if m_img else None
        m_type = re.search(r'"type"\s*:\s*"([^"]+)"', page)
        typ = (m_type.group(1) if m_type else "").lower()
        if "case" in typ or "container" in typ:
            cat = "Kiste"
        elif "sticker" in typ:
            cat = "Sticker"
        elif "agent" in typ:
            cat = "Agent"
        elif "key" in typ:
            cat = "Schlüssel"
        elif "patch" in typ:
            cat = "Patch"
        elif "music" in typ:
            cat = "Musik-Kit"
        else:
            cat = "Waffen-Skin"
        return (name, icon, cat)
    except Exception:
        return (mh, None, None)

# -------------------------- Routen -------------------------------

def select_items(con: sqlite3.Connection):
    cols = [
        "i.id", "i.display_name", "i.market_hash", "i.buy_price_cents"
    ]
    cols.append("i.icon_url" if has_column(con, "items", "icon_url") else "NULL AS icon_url")
    cols.append("i.category" if has_column(con, "items", "category") else "NULL AS category")
    cols.append("IFNULL(i.is_active,1) AS is_active" if has_column(con, "items", "is_active") else "1 AS is_active")
    sql = f"SELECT {', '.join(cols)} FROM items i ORDER BY i.display_name"
    return con.execute(sql).fetchall()

@app.get("/")
def index():
    sel_cat = request.args.get("cat", "Alle")
    con = connect()
    rows = select_items(con)
    items = [item_row_to_dict(con, r) for r in rows]
    con.close()

    if sel_cat != "Alle":
        items = [it for it in items if (it["cat"] or "Unbekannt") == sel_cat]

    cats = sorted({(it["cat"] or "Unbekannt") for it in items} | {"Alle"})
    return render_template("index.html",
                           categories=cats,
                           items=items,
                           selected=None,
                           now_ts=int(time.time()))

@app.get("/item/<int:item_id>")
def item(item_id: int):
    sel_cat = request.args.get("cat", "Alle")
    con = connect()
    r = con.execute("""
        SELECT i.id, i.display_name, i.market_hash, i.buy_price_cents,
               i.icon_url, i.category, IFNULL(i.is_active,1) AS is_active
        FROM items i WHERE i.id=?
    """, (item_id,)).fetchone()
    if not r:
        con.close()
        return redirect(url_for("index"))

    it = item_row_to_dict(con, r)
    chart = build_chart_payload(con, item_id, it["buy"])

    rows = select_items(con)
    items = [item_row_to_dict(con, x) for x in rows]
    con.close()

    cats = sorted({(x["cat"] or "Unbekannt") for x in items} | {"Alle"})
    if sel_cat != "Alle":
        items = [x for x in items if (x["cat"] or "Unbekannt") == sel_cat]

    alert_th = get_threshold(item_id)
    return render_template(
        "index.html",
        categories=cats,
        items=items,
        selected={"it": it, "chart": chart, "alert_th": alert_th},
        now_ts=int(time.time())
    )

# ------------------------- Alerts --------------------------------

def get_threshold(item_id: int) -> Optional[float]:
    con = connect()
    try:
        ensure_alerts_table(con)
        row = con.execute("SELECT threshold_net_eur FROM alerts WHERE item_id=?", (item_id,)).fetchone()
        return None if not row else float(row[0]) if row[0] is not None else None
    finally:
        con.close()

def ensure_alerts_table(con: sqlite3.Connection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            item_id INTEGER PRIMARY KEY,
            threshold_net_eur REAL,
            above_threshold INTEGER DEFAULT 0
        )
    """)

@app.post("/alert/<int:item_id>")
def set_alert(item_id: int):
    raw = (request.form.get("threshold") or "").strip().replace(",", ".")
    try:
        th = float(raw) if raw else None
    except ValueError:
        th = None

    con = connect()
    ensure_alerts_table(con)

    # Item-Namen für Benachrichtigung
    item_name = con.execute("SELECT display_name FROM items WHERE id=?", (item_id,)).fetchone()
    item_name = item_name[0] if item_name else f"Item #{item_id}"

    if th is None:
        con.execute("DELETE FROM alerts WHERE item_id=?", (item_id,))
        con.commit()
        msg = f"❌ Preisalarm für {html.escape(item_name)} wurde gelöscht."
        flash(msg, "info")
    else:
        con.execute("""
            INSERT INTO alerts(item_id, threshold_net_eur, above_threshold)
            VALUES(?, ?, 0)
            ON CONFLICT(item_id) DO UPDATE SET
              threshold_net_eur=excluded.threshold_net_eur,
              above_threshold=0
        """, (item_id, th))
        con.commit()
        msg = f"✅ Preisalarm für {html.escape(item_name)} eingerichtet: ab € {th:.2f} (Netto)."
        flash(msg, "success")
        try:
            tg_send(f"✅ <b>{html.escape(item_name)}</b> – ab € {th:.2f}")
        except Exception as e:
            print(f"[Telegram] Fehler beim Versand: {e}")
    
    con.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return ("OK", 200)
    return redirect(url_for("item", item_id=item_id, **({"cat": request.args.get("cat")} if request.args.get("cat") else {})))

# --------------------- ADD / EDIT / TOGGLE / DELETE --------------

@app.get("/add")
def add():
    sel_cat = request.args.get("cat", "Alle")
    dummy = {
        "id": None,
        "display_name": "",
        "steam_url": "",
        "market_hash": "",
        "buy": None,
        "buy_eur": "",
        "category": (sel_cat if sel_cat != "Alle" else ""),
        "is_active": 1,
    }
    return render_template("add.html", it=dummy,
                           categories=["Waffen-Skin","Sticker","Agent","Kiste","Schlüssel","Patch","Musik-Kit","Unbekannt"])

@app.post("/add")
def add_post():
    name_in   = (request.form.get("name") or "").strip()
    steam_url = (request.form.get("steam_url") or "").strip()
    mh_in     = (request.form.get("market_hash") or "").strip()
    buy_raw   = (request.form.get("buy") or request.form.get("buy_eur") or "").strip().replace(",", ".")

    # Market-Hash bestimmen
    mh = _parse_market_hash_from_url(steam_url) if steam_url else mh_in
    if not mh:
        return render_template("add.html",
            it={"display_name": name_in, "steam_url": steam_url, "market_hash": mh_in, "buy": None, "buy_eur": buy_raw, "category": "", "is_active": 1},
            categories=["Waffen-Skin","Sticker","Agent","Kiste","Schlüssel","Patch","Musik-Kit","Unbekannt"],
            error="Bitte eine gültige Steam-Market-URL oder einen Market-Hash angeben."
        )

    # Meta holen: nutze die Search-API (render) für exakte Treffer
    disp, icon, cat = _fetch_meta_for_hash(mh)
    if name_in:
        disp = name_in

    # Kaufpreis wandeln
    try:
        buy_cents = int(round(float(buy_raw) * 100)) if buy_raw else None
    except ValueError:
        buy_cents = None

    # Insert Item
    con = connect()
    con.execute("""
        INSERT INTO items (display_name, market_hash, buy_price_cents, icon_url, category, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (disp, mh, buy_cents, icon, cat))
    new_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.commit()
    con.close()

    # Direkt Preissnapshot holen & speichern (falls abrufbar)
    cur_cents = fetch_price_cents(mh)
    if cur_cents is not None:
        insert_price_snapshot(new_id, cur_cents)

    # Versuch: Icon sofort auto-fetchen (falls bei _fetch_meta_for_hash kein Icon geliefert wurde)
    try:
        if not icon:
            from fetch_icons import steam_icon
            fetched = steam_icon(mh)
            if fetched:
                # handle FALLBACK:: marker
                if isinstance(fetched, str) and fetched.startswith("FALLBACK::"):
                    fetched = fetched.split("FALLBACK::", 1)[1]
                # store into DB
                con2 = connect()
                con2.execute("UPDATE items SET icon_url=? WHERE id=?", (fetched, new_id))
                con2.commit(); con2.close()
    except Exception:
        pass

    return redirect(url_for("item", item_id=new_id))

# ---- Edit (GET) --------------------------------------------------

@app.get("/item/<int:item_id>/edit")
def edit_item_get(item_id: int):
    sel_cat = request.args.get("cat", "Alle")

    con = connect()
    row = con.execute("""
        SELECT i.id, i.display_name, i.market_hash, i.buy_price_cents,
               i.icon_url, i.category,
               IFNULL(i.is_active, 1) AS is_active
        FROM items i
        WHERE i.id=?
    """, (item_id,)).fetchone()
    con.close()

    if not row:
        return redirect(url_for("index"))

    it = {
        "id":           row["id"],
        "display_name": row["display_name"],
        "market_hash":  row["market_hash"],
        "buy":          eur(row["buy_price_cents"]),
        "icon_url":     row["icon_url"],
        "category":     row["category"],
        "active":       int(row["is_active"]),
    }

    cats = ["Waffen-Skin","Sticker","Agent","Kiste","Schlüssel","Patch","Musik-Kit","Unbekannt"]
    return render_template("edit.html", it=it, sel_cat=sel_cat, categories=cats)

# ---- Edit speichern ----------------------------------------------

@app.post("/item/<int:item_id>/edit")
def update_item(item_id: int):
    name_in   = (request.form.get("name") or "").strip()
    steam_url = (request.form.get("steam_url") or "").strip()
    buy_raw   = (request.form.get("buy") or request.form.get("buy_eur") or "").strip().replace(",", ".")
    cat_in    = (request.form.get("category") or "").strip() or None

    con = connect()
    r = con.execute("SELECT display_name, market_hash FROM items WHERE id=?", (item_id,)).fetchone()
    if not r:
        con.close()
        return redirect(url_for("index"))

    display_name = r["display_name"]
    market_hash  = r["market_hash"]
    icon = None

    if steam_url:
        mh_new = _parse_market_hash_from_url(steam_url)
        if mh_new:
            market_hash = mh_new
            # Hole Metadaten via Search-API
            dname, icon, auto_cat = _fetch_meta_for_hash(market_hash)
            display_name = dname
            if not cat_in:
                cat_in = auto_cat

    if name_in:
        display_name = name_in

    try:
        buy_cents = int(round(float(buy_raw) * 100)) if buy_raw else None
    except ValueError:
        buy_cents = None

    # allow manual icon override from the edit form
    icon_in = (request.form.get("icon_url") or "").strip() or None

    sets = ["display_name = ?", "market_hash = ?", "buy_price_cents = ?", "category = ?"]
    vals: list[Any] = [display_name, market_hash, buy_cents, cat_in]
    # priority: manual icon from form > fetched icon
    if icon_in is not None:
        sets.append("icon_url = ?")
        vals.append(icon_in)
    elif icon is not None:
        sets.append("icon_url = ?")
        vals.append(icon)
    vals.append(item_id)

    con.execute(f"UPDATE items SET {', '.join(sets)} WHERE id=?", vals)
    con.commit(); con.close()
    return redirect(url_for("item", item_id=item_id))

# ---- Aktivieren/Deaktivieren ------------------------------------

@app.post("/item/<int:item_id>/status")
def set_item_status(item_id: int):
    """Aktiv/Deaktiviert toggeln und wieder zurück zum Edit-Dialog."""
    sel_cat = request.args.get("cat")

    con = connect()
    try:
        row = con.execute(
            "SELECT IFNULL(is_active,1) AS is_active FROM items WHERE id=?",
            (item_id,)
        ).fetchone()
        if not row:
            return redirect(url_for("index", **({"cat": sel_cat} if sel_cat else {})))

        cur = int(row["is_active"])
        new = 0 if cur == 1 else 1

        con.execute("UPDATE items SET is_active=? WHERE id=?", (new, item_id))
        con.commit()
    finally:
        con.close()

    return redirect(url_for("edit_item_get", item_id=item_id,
                            **({"cat": sel_cat} if sel_cat else {})))

# ---- Löschen -----------------------------------------------------

@app.post("/item/<int:item_id>/delete")
def delete_item(item_id: int):
    con = connect()
    con.execute("DELETE FROM prices WHERE item_id=?", (item_id,))
    con.execute("DELETE FROM alerts WHERE item_id=?", (item_id,))
    con.execute("DELETE FROM items WHERE id=?", (item_id,))
    con.commit(); con.close()
    return redirect(url_for("index"))

# ---- Einzel-Refresh (Preis jetzt holen) --------------------------

@app.post("/item/<int:item_id>/refresh")
def refresh_item(item_id: int):
    con = connect()
    r = con.execute("SELECT market_hash FROM items WHERE id=?", (item_id,)).fetchone()
    con.close()
    if not r:
        return redirect(url_for("index"))
    mh = r["market_hash"]
    cents = fetch_price_cents(mh)
    if cents is not None:
        insert_price_snapshot(item_id, cents)
    return redirect(url_for("item", item_id=item_id))

# --------------------------- API ---------------------------------

@app.get("/api/item/<int:item_id>")
def api_item(item_id: int):
    con = connect()
    r = con.execute("SELECT id, buy_price_cents FROM items WHERE id=?", (item_id,)).fetchone()
    if not r:
        con.close()
        return jsonify({"ok": False}), 404
    buy = eur(r["buy_price_cents"])
    payload = build_chart_payload(con, item_id, buy)
    con.close()
    return jsonify(payload)

# -------------------------- Start --------------------------------

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"})
