CS2 Tracker – Quick Start
=========================

1) Virtualenv & Install
-----------------------
python -m venv venv
# Windows:
source venv/Scripts/activate
# Linux/Mac:
# source venv/bin/activate
pip install -r requirements.txt

2) Datenbank anlegen
--------------------
python init_db.py

3) App starten
--------------
python app.py
-> http://127.0.0.1:5000

4) Items pflegen & Preise holen
-------------------------------
- In der Web-UI auf "+ Hinzufügen".
- Preise schreiben (jede halbe Stunde per Task/Scheduler):
  python fetch_all.py

5) Alerts (optional, Telegram)
------------------------------
.env im Projekt:
TELEGRAM_BOT_TOKEN=123:ABC
TELEGRAM_CHAT_ID=12345678

fetch_all.py markiert Alerts in der DB (last_alert_ts).
Den Versand kannst du mit telegram_util.tg_send() übernehmen.
