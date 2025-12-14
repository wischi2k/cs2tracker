#!/usr/bin/env python3
import sqlite3
DB = 'cs2_prices.sqlite'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# Find Neo-Noir
row = con.execute("SELECT id FROM items WHERE market_hash LIKE '%Neo-Noir%'").fetchone()
if row:
    item_id = row['id']
    # Delete all price snapshots for this item
    con.execute("DELETE FROM prices WHERE item_id=?", (item_id,))
    con.commit()
    print(f"✓ Gelöscht alle Preisdaten für item_id={item_id}")
else:
    print("Kein Neo-Noir Item gefunden")

con.close()
