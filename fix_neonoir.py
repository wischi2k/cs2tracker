#!/usr/bin/env python3
# Fix the wrong M4A4 item (delete and log, so you can re-add it with correct meta)
import sqlite3

DB = 'cs2_prices.sqlite'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# Find the wrong item
row = con.execute("SELECT id, display_name, market_hash FROM items WHERE market_hash LIKE '%Neo-Noir%'").fetchone()
if row:
    item_id = row['id']
    print(f"Lösche falsches Item:")
    print(f"  id: {item_id}")
    print(f"  display_name: {row['display_name']}")
    print(f"  market_hash: {row['market_hash']}")
    
    # Delete prices and alerts
    con.execute("DELETE FROM prices WHERE item_id=?", (item_id,))
    con.execute("DELETE FROM alerts WHERE item_id=?", (item_id,))
    con.execute("DELETE FROM items WHERE id=?", (item_id,))
    con.commit()
    print(f"✓ Gelöscht")
else:
    print("Kein Item mit 'Neo-Noir' gefunden")

con.close()
