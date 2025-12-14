import sqlite3

con = sqlite3.connect('cs2_prices.sqlite')
con.row_factory = sqlite3.Row
r = con.execute("SELECT id, market_hash, icon_url FROM items WHERE market_hash LIKE ?", ('%Neo-Noir%',)).fetchone()
if not r:
    print('NO_ROW')
else:
    print('ID:', r['id'])
    print('MARKET_HASH:', r['market_hash'])
    print('ICON_URL:', r['icon_url'])
con.close()
