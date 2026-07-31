from __future__ import annotations

import time
from typing import Any

from app.db import get_connection


class ItemRepository:
    def ensure_schema(self) -> None:
        con = get_connection()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    display_name TEXT NOT NULL,
                    market_hash TEXT NOT NULL,
                    buy_price_cents INTEGER,
                    icon_url TEXT,
                    icon_updated_at INTEGER DEFAULT 0,
                    category TEXT,
                    is_active INTEGER DEFAULT 1
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    item_id INTEGER NOT NULL,
                    ts INTEGER NOT NULL,
                    price_cents INTEGER NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    item_id INTEGER PRIMARY KEY,
                    threshold_net_eur REAL,
                    above_threshold INTEGER DEFAULT 0
                )
                """
            )
            cols = {r["name"] for r in con.execute("PRAGMA table_info(items)").fetchall()}
            if "icon_url" not in cols:
                con.execute("ALTER TABLE items ADD COLUMN icon_url TEXT")
            if "category" not in cols:
                con.execute("ALTER TABLE items ADD COLUMN category TEXT")
            if "icon_updated_at" not in cols:
                con.execute("ALTER TABLE items ADD COLUMN icon_updated_at INTEGER DEFAULT 0")
            if "is_active" not in cols:
                con.execute("ALTER TABLE items ADD COLUMN is_active INTEGER DEFAULT 1")
            if "item_type" not in cols:
                con.execute("ALTER TABLE items ADD COLUMN item_type TEXT NOT NULL DEFAULT 'inventory'")
                con.execute("UPDATE items SET item_type='inventory' WHERE item_type IS NULL OR item_type NOT IN ('inventory','tracking')")

            alert_cols = {r["name"] for r in con.execute("PRAGMA table_info(alerts)").fetchall()}
            if "triggered_at" not in alert_cols:
                con.execute("ALTER TABLE alerts ADD COLUMN triggered_at INTEGER")

            con.execute("CREATE INDEX IF NOT EXISTS idx_prices_item_ts ON prices(item_id, ts DESC)")
            con.commit()
        finally:
            con.close()

    def list_items_with_latest_price(self) -> list[dict[str, Any]]:
        con = get_connection()
        try:
            rows = con.execute(
                """
                SELECT
                    i.id,
                    i.display_name,
                    i.market_hash,
                    i.buy_price_cents,
                    i.icon_url,
                    IFNULL(i.icon_updated_at,0) AS icon_updated_at,
                    i.category,
                    IFNULL(i.is_active,1) AS is_active,
                    IFNULL(i.item_type,'inventory') AS item_type,
                    (
                        SELECT p.price_cents
                        FROM prices p
                        WHERE p.item_id = i.id
                        ORDER BY p.ts DESC
                        LIMIT 1
                    ) AS current_price_cents
                FROM items i
                ORDER BY i.display_name
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()

    def get_item_with_latest_price(self, item_id: int) -> dict[str, Any] | None:
        con = get_connection()
        try:
            row = con.execute(
                """
                SELECT
                    i.id,
                    i.display_name,
                    i.market_hash,
                    i.buy_price_cents,
                    i.icon_url,
                    IFNULL(i.icon_updated_at,0) AS icon_updated_at,
                    i.category,
                    IFNULL(i.is_active,1) AS is_active,
                    IFNULL(i.item_type,'inventory') AS item_type,
                    (
                        SELECT p.price_cents
                        FROM prices p
                        WHERE p.item_id = i.id
                        ORDER BY p.ts DESC
                        LIMIT 1
                    ) AS current_price_cents
                FROM items i
                WHERE i.id=?
                """,
                (item_id,),
            ).fetchone()
            return None if row is None else dict(row)
        finally:
            con.close()

    def get_chart_series(self, item_id: int) -> tuple[list[int], list[int]]:
        con = get_connection()
        try:
            rows = con.execute(
                "SELECT ts, price_cents FROM prices WHERE item_id=? ORDER BY ts ASC",
                (item_id,),
            ).fetchall()
            return ([int(r["ts"]) for r in rows], [int(r["price_cents"]) for r in rows])
        finally:
            con.close()

    def list_active_items_basic(self) -> list[dict[str, Any]]:
        con = get_connection()
        try:
            rows = con.execute(
                """
                SELECT i.id, i.display_name, i.buy_price_cents, i.market_hash,
                       IFNULL(i.item_type,'inventory') AS item_type,
                       a.threshold_net_eur, a.above_threshold
                FROM items i
                LEFT JOIN alerts a ON a.item_id = i.id AND a.threshold_net_eur IS NOT NULL
                WHERE IFNULL(i.is_active,1)=1
                ORDER BY i.display_name
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()

    def get_price_at_or_before(self, item_id: int, ts: int) -> int | None:
        con = get_connection()
        try:
            row = con.execute(
                """
                SELECT price_cents
                FROM prices
                WHERE item_id=? AND ts<=?
                ORDER BY ts DESC
                LIMIT 1
                """,
                (item_id, int(ts)),
            ).fetchone()
            return None if row is None else int(row[0])
        finally:
            con.close()

    def get_price_at_or_after(self, item_id: int, ts: int) -> int | None:
        con = get_connection()
        try:
            row = con.execute(
                """
                SELECT price_cents
                FROM prices
                WHERE item_id=? AND ts>=?
                ORDER BY ts ASC
                LIMIT 1
                """,
                (item_id, int(ts)),
            ).fetchone()
            return None if row is None else int(row[0])
        finally:
            con.close()

    def get_latest_price_cents(self, item_id: int) -> int | None:
        con = get_connection()
        try:
            row = con.execute(
                """
                SELECT price_cents
                FROM prices
                WHERE item_id=?
                ORDER BY ts DESC
                LIMIT 1
                """,
                (item_id,),
            ).fetchone()
            return None if row is None else int(row[0])
        finally:
            con.close()

    def get_alert_threshold(self, item_id: int) -> float | None:
        data = self.get_alert_data(item_id)
        return data["threshold"] if data else None

    def get_alert_data(self, item_id: int) -> dict[str, Any] | None:
        con = get_connection()
        try:
            row = con.execute(
                "SELECT threshold_net_eur, above_threshold, triggered_at FROM alerts WHERE item_id=?",
                (item_id,),
            ).fetchone()
            if row is None:
                return None
            return {
                "threshold": float(row[0]) if row[0] is not None else None,
                "above": bool(int(row[1] or 0)),
                "triggered_at": int(row[2]) if row[2] is not None else None,
            }
        finally:
            con.close()

    def upsert_alert_threshold(self, item_id: int, threshold: float, above: bool = True) -> None:
        con = get_connection()
        try:
            con.execute(
                """
                INSERT INTO alerts(item_id, threshold_net_eur, above_threshold)
                VALUES(?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    threshold_net_eur=excluded.threshold_net_eur,
                    above_threshold=excluded.above_threshold
                """,
                (item_id, threshold, 1 if above else 0),
            )
            con.commit()
        finally:
            con.close()

    def delete_alert_threshold(self, item_id: int) -> None:
        con = get_connection()
        try:
            con.execute("DELETE FROM alerts WHERE item_id=?", (item_id,))
            con.commit()
        finally:
            con.close()

    def fire_alert(self, item_id: int) -> None:
        """Mark alert as fired: record triggered_at, clear threshold (keeps row for chart marker)."""
        con = get_connection()
        try:
            con.execute(
                """
                UPDATE alerts
                SET threshold_net_eur=NULL, triggered_at=?
                WHERE item_id=?
                """,
                (int(time.time()), item_id),
            )
            con.commit()
        finally:
            con.close()

    def get_items_with_active_alerts(self) -> list[dict[str, Any]]:
        con = get_connection()
        try:
            rows = con.execute(
                """
                SELECT
                    i.id,
                    i.display_name,
                    IFNULL(i.item_type,'inventory') AS item_type,
                    a.threshold_net_eur,
                    a.above_threshold,
                    (
                        SELECT p.price_cents
                        FROM prices p
                        WHERE p.item_id = i.id
                        ORDER BY p.ts DESC
                        LIMIT 1
                    ) AS current_price_cents
                FROM items i
                JOIN alerts a ON a.item_id = i.id
                WHERE a.threshold_net_eur IS NOT NULL
                AND IFNULL(i.is_active, 1) = 1
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()

    def get_item_name(self, item_id: int) -> str | None:
        con = get_connection()
        try:
            row = con.execute("SELECT display_name FROM items WHERE id=?", (item_id,)).fetchone()
            return None if row is None else str(row[0])
        finally:
            con.close()

    def promote_to_inventory(self, item_id: int, buy_price_cents: int | None) -> None:
        con = get_connection()
        try:
            con.execute(
                "UPDATE items SET item_type='inventory', buy_price_cents=? WHERE id=?",
                (buy_price_cents, item_id),
            )
            con.commit()
        finally:
            con.close()

    def insert_item(
        self,
        display_name: str,
        market_hash: str,
        buy_price_cents: int | None,
        icon_url: str | None,
        category: str | None,
        item_type: str = "inventory",
    ) -> int:
        con = get_connection()
        try:
            con.execute(
                """
                INSERT INTO items (display_name, market_hash, buy_price_cents, icon_url, category, is_active, item_type)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (display_name, market_hash, buy_price_cents, icon_url, category, item_type),
            )
            if icon_url and icon_url.strip():
                con.execute(
                    "UPDATE items SET icon_updated_at=? WHERE id=last_insert_rowid()",
                    (int(time.time()),),
                )
            new_id = int(con.execute("SELECT last_insert_rowid()").fetchone()[0])
            con.commit()
            return new_id
        finally:
            con.close()

    def update_item(
        self,
        item_id: int,
        display_name: str,
        market_hash: str,
        buy_price_cents: int | None,
        category: str | None,
        icon_url: str | None,
        item_type: str | None = None,
    ) -> None:
        con = get_connection()
        try:
            if item_type is not None:
                con.execute(
                    """
                    UPDATE items
                    SET
                        display_name=?,
                        market_hash=?,
                        buy_price_cents=?,
                        category=?,
                        icon_url=?,
                        item_type=?,
                        icon_updated_at=CASE
                            WHEN COALESCE(icon_url,'') <> COALESCE(?, '')
                            THEN ?
                            ELSE IFNULL(icon_updated_at,0)
                        END
                    WHERE id=?
                    """,
                    (
                        display_name,
                        market_hash,
                        buy_price_cents,
                        category,
                        icon_url,
                        item_type,
                        icon_url,
                        int(time.time()),
                        item_id,
                    ),
                )
            else:
                con.execute(
                    """
                    UPDATE items
                    SET
                        display_name=?,
                        market_hash=?,
                        buy_price_cents=?,
                        category=?,
                        icon_url=?,
                        icon_updated_at=CASE
                            WHEN COALESCE(icon_url,'') <> COALESCE(?, '')
                            THEN ?
                            ELSE IFNULL(icon_updated_at,0)
                        END
                    WHERE id=?
                    """,
                    (
                        display_name,
                        market_hash,
                        buy_price_cents,
                        category,
                        icon_url,
                        icon_url,
                        int(time.time()),
                        item_id,
                    ),
                )
            con.commit()
        finally:
            con.close()

    def toggle_item_status(self, item_id: int) -> None:
        con = get_connection()
        try:
            row = con.execute("SELECT IFNULL(is_active,1) AS is_active FROM items WHERE id=?", (item_id,)).fetchone()
            if row is None:
                return
            new_status = 0 if int(row["is_active"]) == 1 else 1
            con.execute("UPDATE items SET is_active=? WHERE id=?", (new_status, item_id))
            con.commit()
        finally:
            con.close()

    def delete_item(self, item_id: int) -> None:
        con = get_connection()
        try:
            con.execute("DELETE FROM prices WHERE item_id=?", (item_id,))
            con.execute("DELETE FROM alerts WHERE item_id=?", (item_id,))
            con.execute("DELETE FROM items WHERE id=?", (item_id,))
            con.commit()
        finally:
            con.close()

    def insert_price_snapshot(self, item_id: int, price_cents: int) -> None:
        con = get_connection()
        try:
            con.execute(
                "INSERT INTO prices(item_id, ts, price_cents) VALUES(?,?,?)",
                (item_id, int(time.time()), int(price_cents)),
            )
            con.commit()
        finally:
            con.close()
