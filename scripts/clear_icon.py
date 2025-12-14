import sqlite3
con = sqlite3.connect('cs2_prices.sqlite')
con.execute("UPDATE items SET icon_url=NULL WHERE market_hash LIKE '%Neo-Noir%'")
con.commit()
con.close()
print('✓ Icon gelöscht')
