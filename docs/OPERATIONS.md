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
User=cs2
WorkingDirectory=/home/cs2/cs2tracker_full_package_arch
EnvironmentFile=/home/cs2/cs2tracker_full_package_arch/.env
ExecStart=/home/cs2/cs2tracker_full_package_arch/.venv/bin/python -m scripts.fetch_all_prices
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

- `GET /` Uebersicht
- `GET /item/<id>` Detailansicht
- `POST /add` Item anlegen
- `POST /item/<id>/edit` Item speichern
- `POST /item/<id>/refresh` Preis aktualisieren
- `POST /alert/<id>` Alert setzen/loeschen
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

## Automatisches Deployment via GitHub Actions (Self-Hosted Runner)

### Überblick

Beim Push auf `main` zieht der GitHub Actions Runner auf dem NUC automatisch die neuen Dateien und startet den Service neu. Keine manuelle SSH-Session nötig.

```
git push origin main
       │
       ▼
GitHub Actions Workflow
       │
       ▼
Self-Hosted Runner auf dem NUC
       ├── git pull
       ├── pip install -r requirements.txt
       └── systemctl restart cs2tracker
```

---

### Einmalige Migration (alter → git-basierter Stand)

Führe auf dem Server aus:

```bash
# 1. Installationspfad herausfinden
find /home /opt /srv -name "run.py" 2>/dev/null

# 2. Migrationsskript anpassen und ausführen
nano ~/migrate_to_git.sh         # OLD_DIR setzen
bash ~/migrate_to_git.sh
```

Das Skript liegt unter `scripts/migrate_to_git.sh` im Repository.
Es sichert die Datenbank und .env, klont das Repo an den gleichen Ort und stellt DB + .env wieder her.

---

### Self-Hosted Runner einrichten

**Einmalig auf dem Debian-Server als Benutzer `cs2`:**

```bash
# 1. Runner-Verzeichnis anlegen
mkdir -p ~/actions-runner && cd ~/actions-runner

# 2. Runner herunterladen (aktuelle Version von https://github.com/actions/runner/releases)
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.322.0/actions-runner-linux-x64-2.322.0.tar.gz
tar xzf actions-runner-linux-x64.tar.gz

# 3. Runner registrieren (Token aus GitHub holen, siehe unten)
./config.sh \
  --url https://github.com/wischi2k/cs2tracker \
  --token DEIN_RUNNER_TOKEN \
  --name nuc-debian \
  --labels self-hosted,linux \
  --work _work \
  --unattended

# 4. Als systemd-Service installieren (läuft auch nach Reboot)
sudo ./svc.sh install cs2
sudo ./svc.sh start
sudo ./svc.sh status
```

**Runner-Token holen:**
GitHub → Repository → Settings → Actions → Runners → „New self-hosted runner" → Token kopieren (gilt 1 Stunde).

---

### APP_DIR Variable in GitHub setzen

```
GitHub → Repository → Settings → Secrets and variables → Actions → Variables → New repository variable
  Name:  APP_DIR
  Value: /opt/cs2tracker      ← deinen tatsächlichen Pfad eintragen
```

---

### sudo-Rechte für systemctl (passwordless)

Damit der Runner `systemctl restart cs2tracker` ohne Passwort ausführen darf:

```bash
sudo visudo -f /etc/sudoers.d/cs2tracker-deploy
```

Inhalt:

```
cs2 ALL=(ALL) NOPASSWD: /bin/systemctl restart cs2tracker, /bin/systemctl start cs2tracker, /bin/systemctl stop cs2tracker, /bin/systemctl is-active cs2tracker
```

---

### Deployment testen

```bash
# Lokal auf dem Entwicklungsrechner:
git add .
git commit -m "test: deploy pipeline"
git push origin main

# Auf GitHub: Actions → laufender Workflow beobachten
# Auf dem Server:
sudo systemctl status cs2tracker
journalctl -u cs2tracker -n 20
```

---

### Fehlerbehebung

| Problem | Lösung |
|---|---|
| Runner offline | `sudo ~/actions-runner/svc.sh status` → ggf. starten |
| `git reset --hard` schlägt fehl | Untracked files: `git clean -fd` im APP_DIR |
| Service startet nicht | `journalctl -u cs2tracker -n 50` |
| pip-Fehler | `.venv` löschen und neu anlegen: `python3 -m venv .venv` |

---

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
