import sqlite3, time
DB='cs2_prices.sqlite'
con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row
mh = 'M4A4 | Neo-Noir (Minimal Wear)'
rows = con.execute("SELECT id, display_name, market_hash, icon_url, buy_price_cents FROM items WHERE market_hash=? OR display_name LIKE ?", (mh, '%Neo-Noir%')).fetchall()
if not rows:
    print('Kein Item gefunden für Neo-Noir')
else:
    for r in rows:
        item_id=r['id']
        print('---')
        print('id:', item_id)
        print('display_name:', r['display_name'])
        print('market_hash:', r['market_hash'])
        print('icon_url:', r['icon_url'])
        print('buy_price_cents:', r['buy_price_cents'])
        p = con.execute('SELECT ts, price_cents FROM prices WHERE item_id=? ORDER BY ts DESC LIMIT 1', (item_id,)).fetchone()
        if p:
            print('latest price ts:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p['ts'])))
            print('latest price eur:', p['price_cents']/100.0)
        else:
            print('Keine Preisdaten vorhanden')
        count = con.execute('SELECT COUNT(*) as c FROM prices WHERE item_id=?', (item_id,)).fetchone()['c']
        print('price snapshots count:', count)
        alert = con.execute('SELECT threshold_net_eur, above_threshold FROM alerts WHERE item_id=?', (item_id,)).fetchone()
        print('alert:', dict(alert) if alert else None)
con.close()
