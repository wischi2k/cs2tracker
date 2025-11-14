# migrate_add_steam_category.py
import sqlite3

DB = "cs2_prices.sqlite"

def guess_category(name: str | None) -> str:
    n = (name or "").lower()
    if "agent" in n or "mccoy" in n or "sabre" in n:
        return "Agent"
    if "music" in n or "kit" in n or "bbno" in n:
        return "Music Kit"
    return "Waffen-Skin"

con = sqlite3.connect(DB)
cur = con.cursor()

# Vorhandene Spalten ermitteln
cols = {row[1] for row in cur.execute("PRAGMA table_info(items)")}

# Spalten bei Bedarf hinzufügen
if "steam_url" not in cols:
    print(">> Adding column items.steam_url ...")
    cur.execute("ALTER TABLE items ADD COLUMN steam_url TEXT")

if "category" not in cols:
    print(">> Adding column items.category ...")
    cur.execute("ALTER TABLE items ADD COLUMN category TEXT")

# Kategorien sinnvoll vorbelegen, falls leer
cur.execute("SELECT id, display_name, market_hash FROM items WHERE category IS NULL OR category=''")
rows = cur.fetchall()
for _id, dn, mh in rows:
    cat = guess_category(dn or mh)
    cur.execute("UPDATE items SET category=? WHERE id=?", (cat, _id))

con.commit()
con.close()
print("Migration done.")
