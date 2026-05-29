# Nutzung und Betrieb

## Konfiguration

Umgebungsvariablen:

- `FLASK_SECRET_KEY`: Secret fuer Flask Session/Flash und Secret-Verschluesselung
- `FLASK_DEBUG`: `1/true/on` fuer Debug-Modus
- `CS2_DB_PATH`: Pfad zur SQLite-Datei
- `FLASK_HOST`: Bind-Adresse (`127.0.0.1` nur lokal, `0.0.0.0` fuer LAN)
- `FLASK_PORT`: Port (Default `5000`)
- `TELEGRAM_BOT_TOKEN`: optionaler Fallback
- `TELEGRAM_CHAT_ID`: optionaler Fallback

Hinweis: Bei aktivem Setup werden Telegram-Werte verschluesselt in SQLite gespeichert.

## Start

```bash
python run.py
```

Healthcheck:

```bash
curl http://127.0.0.1:5000/health
```

## Preis-Snapshots aktualisieren

Standard:

- Die App fuehrt Auto-Refresh intern aus (Intervall aus Setup/Settings).
- Status ist ueber `/health` unter `auto_refresh` sichtbar.

Manuell (Debug/Adhoc):

```bash
python -m scripts.fetch_all_prices
```

Optionaler Fallback (systemd timer, z. B. fuer streng kontrollierte Server-Jobs):

Service `/etc/systemd/system/cs2tracker-fetch.service`:

```ini
[Unit]
Description=CS2 Tracker price fetch

[Service]
Type=oneshot
User=<username>
WorkingDirectory=/home/<username>/cs2tracker_full_package_arch
EnvironmentFile=/home/<username>/cs2tracker_full_package_arch/.env
ExecStart=/home/<username>/cs2tracker_full_package_arch/.venv/bin/python -m scripts.fetch_all_prices
```

Timer `/etc/systemd/system/cs2tracker-fetch.timer`:

```ini
[Unit]
Description=Run CS2 price fetch every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cs2tracker-fetch.timer
sudo systemctl list-timers | grep cs2tracker-fetch
```

Hinweis:

- Entweder nur interner Scheduler (empfohlen fuer einfache Nutzung),
- oder interner Scheduler + systemd-Fallback (hybrid).
- Falls du nur intern fahren willst, optional deaktivieren:

```bash
sudo systemctl disable --now cs2tracker-fetch.timer
```

## Wichtige Endpunkte

- `GET /` Uebersicht (Inventar links, Tracking rechts)
- `GET /item/<id>` Detailansicht
- `POST /add` Item anlegen (Parameter: `item_type=inventory|tracking`)
- `POST /item/<id>/edit` Item speichern
- `POST /item/<id>/promote` Tracking-Item als gekauft markieren → wechselt zu Inventar
- `POST /item/<id>/refresh` Preis aktualisieren
- `POST /alert/<id>` Alert setzen/loeschen (Parameter: `threshold`, `above_threshold=0|1`)
- `GET /api/item/<id>` Chartdaten
- `GET /setup` Setup-Assistent
- `GET /settings` Laufende Konfiguration
- `GET /health` Systemstatus

## Setup-Verhalten

- Wenn `setup_completed=false`, werden normale App-Endpunkte auf `/setup` umgeleitet.
- Zugriffsumfang ist ueber Setup/Settings konfigurierbar:
  - `private_network`: Loopback + private Netze
  - `local_only`: nur Loopback
- Setup-Werte werden in `app_config` gespeichert.
- Telegram-Secrets werden in `secret_store` verschluesselt gespeichert.
- Empfehlung fuer Debian/Proxmox im Heimnetz:
  - `FLASK_HOST=0.0.0.0`
  - Zugriffsumfang in der App auf `private_network`

## Telegram-Zusammenfassung (interner Scheduler)

- Aktivierung und Konfiguration in Setup/Settings:
  - `summary_enabled`
  - `summary_interval_days`
  - `summary_send_time` (`HH:MM`, Server-Zeitzone)
- Versandstatus pruefen:
  - `GET /health` -> `summary.last_status`, `summary.last_sent_ts`, `summary.last_error`

## Betrieb mit systemd (Linux)

Beispiel Unit `/etc/systemd/system/cs2tracker.service`:

```ini
[Unit]
Description=CS2 Tracker
After=network.target

[Service]
User=cs2tracker
Group=cs2tracker
WorkingDirectory=/opt/cs2tracker
Environment="FLASK_SECRET_KEY=change-me"
Environment="FLASK_DEBUG=0"
Environment="CS2_DB_PATH=/opt/cs2tracker/data/cs2_prices.sqlite"
ExecStart=/opt/cs2tracker/.venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cs2tracker
sudo systemctl status cs2tracker
```

## Backups

Sichern:

- Projektverzeichnis
- SQLite-Datei (`CS2_DB_PATH`)
- `.env` (falls genutzt)

Wiederherstellung:

1. Dateien zurueckspielen
2. Service neu starten
3. `/health` pruefen

## Logging

- Aktuell: stdout/stderr
- Empfohlen: `journalctl -u cs2tracker -f`

## Risiken / Grenzen

- SQLite ist kein Multi-Node-DBMS.
- Externe Steam-API kann Rate-Limits/Timeouts haben.
- Telegram ist optional und darf keine Kernfunktion blockieren.
