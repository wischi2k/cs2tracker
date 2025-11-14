import time
import sqlite3
from typing import Optional, List, Dict, Tuple
from telegram_util import tg_send

DB_PATH = "cs2_prices.sqlite"
FEE_RATE = 0.15
DAYS = 7

# Für die Gewinner/Verlierer-Liste:
#   "weekly_change"  -> Veränderung der letzten 7 Tage
#   "profit_vs_buy"  -> Gewinn/Verlust ggü. Kaufpreis
MODE = "weekly_change"

# Bewegungen darunter werden in Top/Flop ignoriert (in %)
MIN_ABS_PCT = 0.1


# ---------- kleine Helfer ----------

def net_eur_from_cents(cents: int) -> float:
    return (cents / 100.0) * (1 - FEE_RATE)

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def price_at_or_before(con: sqlite3.Connection, item_id: int, ts: int) -> Optional[int]:
    row = con.execute("""
        SELECT price_cents FROM prices
        WHERE item_id=? AND ts<=?
        ORDER BY ts DESC LIMIT 1
    """, (item_id, ts)).fetchone()
    return None if not row else int(row[0])

def price_at_or_after(con: sqlite3.Connection, item_id: int, ts: int) -> Optional[int]:
    row = con.execute("""
        SELECT price_cents FROM prices
        WHERE item_id=? AND ts>=?
        ORDER BY ts ASC LIMIT 1
    """, (item_id, ts)).fetchone()
    return None if not row else int(row[0])

def latest_price(con: sqlite3.Connection, item_id: int) -> Optional[int]:
    row = con.execute("""
        SELECT price_cents FROM prices
        WHERE item_id=?
        ORDER BY ts DESC LIMIT 1
    """, (item_id,)).fetchone()
    return None if not row else int(row[0])

def latest_price_safe(con: sqlite3.Connection, item_id: int) -> Optional[int]:
    """Nimmt 'letzter bekannter Preis bis jetzt' (robuster als nur LIMIT 1)."""
    now = int(time.time())
    p = price_at_or_before(con, item_id, now)
    if p is None:
        p = latest_price(con, item_id)
    return p

def first_and_last_for_week(con: sqlite3.Connection, item_id: int, start_ts: int) -> Optional[Tuple[int, int]]:
    baseline = price_at_or_before(con, item_id, start_ts)
    if baseline is None:
        baseline = price_at_or_after(con, item_id, start_ts)
    last = latest_price_safe(con, item_id)
    if baseline is None or last is None:
        return None
    return baseline, last


# ---------- Hauptlogik ----------

def main():
    con = connect()
    now = int(time.time())
    start_ts = now - DAYS * 86400

    items = con.execute("""
        SELECT id, display_name, buy_price_cents, IFNULL(is_active,1) AS act
        FROM items
        WHERE IFNULL(is_active,1)=1
    """).fetchall()

    # ---- Gewinner/Verlierer (wie gehabt) ----
    stats: List[Dict] = []
    for r in items:
        item_id = int(r["id"])
        name = r["display_name"]

        if MODE == "weekly_change":
            pair = first_and_last_for_week(con, item_id, start_ts)
            if not pair:
                continue
            first_c, last_c = pair
            first_n = net_eur_from_cents(first_c)
            last_n  = net_eur_from_cents(last_c)
            if first_n <= 0:
                continue
            delta_eur = last_n - first_n
            pct = (delta_eur / first_n) * 100.0

        else:  # MODE == "profit_vs_buy"
            last_c = latest_price_safe(con, item_id)
            buy_c  = r["buy_price_cents"]
            if last_c is None or buy_c is None or buy_c <= 0:
                continue
            last_n = net_eur_from_cents(last_c)
            buy_n  = net_eur_from_cents(int(buy_c))
            delta_eur = last_n - buy_n
            pct = (delta_eur / buy_n) * 100.0
            first_n = buy_n

        stats.append({
            "name": name,
            "first": round(first_n, 2),
            "last":  round(last_n, 2),
            "delta_eur": round(delta_eur, 2),
            "pct": pct,
        })

    def pick_tops_and_flops(data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        data = [s for s in data if abs(s["pct"]) >= MIN_ABS_PCT]
        if not data:
            return [], []
        gainers = sorted(data, key=lambda x: x["pct"], reverse=True)[:3]
        losers  = []
        used = {g["name"] for g in gainers}
        for s in sorted(data, key=lambda x: x["pct"]):
            if s["name"] not in used:
                losers.append(s)
            if len(losers) == 3:
                break
        return gainers, losers

    gainers, losers = pick_tops_and_flops(stats)

    # ---- Top 5 wertvollste (aktueller Netto-Wert + Δ ggü. Kauf) ----
    valuable: List[Dict] = []
    sum_current_net = 0.0
    sum_buy_net     = 0.0
    buy_count       = 0

    for r in items:
        item_id = int(r["id"])
        name    = r["display_name"]
        last_c  = latest_price_safe(con, item_id)
        if last_c is None:
            continue
        last_n = net_eur_from_cents(last_c)
        sum_current_net += last_n

        profit = None
        if r["buy_price_cents"] is not None:
            buy_n = net_eur_from_cents(int(r["buy_price_cents"]))
            sum_buy_net += buy_n
            buy_count   += 1
            profit = round(last_n - buy_n, 2)

        valuable.append({
            "name": name,
            "last": round(last_n, 2),
            "profit": profit,
        })

    top_valuable = sorted(valuable, key=lambda x: x["last"], reverse=True)[:5]

    # Portfolio-Kennzahlen
    total_current = round(sum_current_net, 2)
    total_buy     = round(sum_buy_net, 2)
    total_pl      = round(total_current - total_buy, 2) if buy_count > 0 else None
    total_pl_pct  = ( (total_pl / total_buy) * 100.0 if (buy_count > 0 and total_buy > 0) else None )

    # ---- Nachricht zusammenbauen ----
    title_scope = "Netto, letzte 7 Tage" if MODE == "weekly_change" else "Netto, vs. Kaufpreis"
    lines = [f"📊 <b>Wöchentliche Zusammenfassung</b> ({title_scope})\n"]

    def fmt(s: Dict) -> str:
        sign = "▲" if s["pct"] >= 0 else "▼"
        return (f"{sign} <b>{s['name']}</b>  {s['pct']:+.2f}%  "
                f"({s['last']:.2f} € / {s['first']:.2f} €; {s['delta_eur']:+.2f} €)")

    lines.append("<b>Top 3 Gewinner</b>")
    if gainers:
        for s in gainers:
            lines.append("• " + fmt(s))
    else:
        lines.append("• – (keine nennenswerten Anstiege)")

    lines.append("\n<b>Top 3 Verlierer</b>")
    if losers:
        for s in losers:
            lines.append("• " + fmt(s))
    else:
        lines.append("• – (keine nennenswerten Rückgänge)")

    # Ø über alle aktiven Items (unabhängig von MIN_ABS_PCT)
    if stats:
        avg_pct = sum(s["pct"] for s in stats) / max(1, len(stats))
        lines.append(f"\nGesamt (Ø aller aktiven Items): {avg_pct:+.2f}%")

    # Depot-Block
    lines.append("\n💼 <b>Depot</b>")
    lines.append(f"• Aktueller Gesamtwert (netto):  {total_current:.2f} €")
    if buy_count > 0:
        lines.append(f"• Investiert (netto, {buy_count} Käufe):  {total_buy:.2f} €")
        lines.append(f"• Gesamt P/L:  {total_pl:+.2f} €"
                     + (f"  ({total_pl_pct:+.2f}%)" if total_pl_pct is not None else ""))
    else:
        lines.append("• Investiert: — (keine Kaufpreise hinterlegt)")

    # Wertvollste
    lines.append("\n💎 <b>Top 5 wertvollste Items</b> (Netto, aktueller Wert)")
    if top_valuable:
        for v in top_valuable:
            if v["profit"] is None:
                lines.append(f"• <b>{v['name']}</b>  {v['last']:.2f} €  (Δ ggü. Kauf: —)")
            else:
                lines.append(f"• <b>{v['name']}</b>  {v['last']:.2f} €  (Δ ggü. Kauf: {v['profit']:+.2f} €)")
    else:
        lines.append("• – (keine Preisdaten vorhanden)")

    tg_send("\n".join(lines))
    con.close()


if __name__ == "__main__":
    main()
