# migrate_add_above_threshold.py
import sqlite3

con = sqlite3.connect("cs2_prices.sqlite")
cols = [r[1] for r in con.execute("PRAGMA table_info(alerts)")]
if "above_threshold" not in cols:
    con.execute("ALTER TABLE alerts ADD COLUMN above_threshold INTEGER DEFAULT 0")
    con.commit()
    print("✅ Spalte 'above_threshold' angelegt.")
else:
    print("ℹ️ Spalte 'above_threshold' existiert bereits.")
con.close()
