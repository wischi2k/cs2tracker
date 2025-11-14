import sqlite3

DB = "cs2_prices.sqlite"

schema = '''
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market_hash TEXT NOT NULL,
  display_name TEXT,
  buy_price_cents INTEGER,
  icon_url TEXT,
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS prices (
  ts INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  price_cents INTEGER NOT NULL,
  FOREIGN KEY (item_id) REFERENCES items(id)
);
CREATE INDEX IF NOT EXISTS idx_prices_item_ts ON prices(item_id, ts);

CREATE TABLE IF NOT EXISTS alerts (
  item_id INTEGER PRIMARY KEY,
  threshold_net_eur INTEGER, -- cents (nullable)
  last_alert_ts INTEGER
);
'''

def main():
    con = sqlite3.connect(DB)
    con.executescript(schema)
    con.commit()
    con.close()
    print("DB initialisiert:", DB)

if __name__ == "__main__":
    main()
