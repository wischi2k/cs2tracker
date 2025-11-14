# migrate_add_icon_column.py
import sqlite3

con = sqlite3.connect("cs2_prices.sqlite")
cols = [r[1] for r in con.execute("PRAGMA table_info(items)")]
if "icon_url" not in cols:
    con.execute("ALTER TABLE items ADD COLUMN icon_url TEXT")
    con.commit()
    print("✅ Spalte 'icon_url' angelegt.")
else:
    print("ℹ️ Spalte 'icon_url' existiert bereits.")
con.close()


