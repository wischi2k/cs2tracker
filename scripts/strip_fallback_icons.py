import sqlite3

con = sqlite3.connect('cs2_prices.sqlite')
con.row_factory = sqlite3.Row
rows = con.execute("SELECT id, icon_url FROM items WHERE icon_url LIKE 'FALLBACK::%'").fetchall()
print('Found', len(rows), 'rows to fix')
for r in rows:
    real = r['icon_url'].split('FALLBACK::',1)[1]
    con.execute('UPDATE items SET icon_url=? WHERE id=?', (real, r['id']))
    print('Fixed', r['id'])
con.commit()
con.close()
