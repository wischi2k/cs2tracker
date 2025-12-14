import sqlite3

url = 'https://community.akamai.steamstatic.com/economy/image/i0CoZ81Ui0m-9KwlBY1L_18myuGuq1wfhWSaZgMttyVfPaERSR0Wqmu7LAocGIGz3UqlXOLrxM-vMGmW8VNxu5Dx60noTyL8ypexwiFO0P_6afBSLvWcMWmfyPxJvOhuRz39wE1142vSztmvInvBOgV0W5R1FLYNuxW4wIbgNrmx4g2Kj4tMmCX93zQJsHgJr0dqFw/330x192?allow_animated=1'

con = sqlite3.connect('cs2_prices.sqlite')
con.row_factory = sqlite3.Row
con.execute('UPDATE items SET icon_url=? WHERE market_hash LIKE ?', (url, '%Neo-Noir%'))
con.commit()
print('Updated rows:', con.execute('SELECT changes()').fetchone()[0])
con.close()
