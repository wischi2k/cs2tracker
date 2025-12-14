import sqlite3, sys
con = sqlite3.connect('cs2_prices.sqlite')
con.row_factory = sqlite3.Row
item_id = int(sys.argv[1]) if len(sys.argv)>1 else 27
r = con.execute('SELECT id, display_name, market_hash, icon_url FROM items WHERE id=?',(item_id,)).fetchone()
if not r:
    print('NO_ROW')
else:
    print('ID:', r['id'])
    print('DISPLAY_NAME:', r['display_name'])
    print('MARKET_HASH:', r['market_hash'])
    print('ICON_URL:', r['icon_url'])
con.close()
