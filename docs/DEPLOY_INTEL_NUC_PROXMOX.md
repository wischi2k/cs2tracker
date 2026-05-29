# Deployment auf Intel NUC mit Proxmox

Stand: 2026-02-08

Diese Anleitung beschreibt eine robuste Zielumgebung fuer CS2 Tracker auf einem Intel NUC mit Proxmox VE.

## 1. Empfohlene Zielarchitektur

- Host: Intel NUC mit Proxmox VE
- Gast: Debian 13 VM (empfohlen) oder Debian LXC
- App: CS2 Tracker als systemd Service
- Reverse Proxy (optional): Nginx/Caddy auf separater VM oder direkt im Gast
- Backup: Proxmox Backup Jobs + Dateibackup von `.env`

Warum VM als Default:

- Einfacheres Debugging bei Python/venv/systemd
- Saubere Trennung gegenueber Host
- Weniger Spezialfaelle als bei unprivilegierten LXC-Containern

## 2. Debian 13 vs Debian 12

Kurz:

- Debian 13 ist die aktuelle Empfehlung fuer neue Setups.
- Debian 12 bleibt eine stabile Alternative, wenn du bereits darauf standardisiert hast.

Begruendung:

- Debian 13 ist aktueller (Pakete/Security-Stand) und wird von den Proxmox Community Scripts explizit per `debian-13-vm.sh` bedient.
- Debian 12 ist konservativer in manchen Produktionsumgebungen, aber fuer einen Neuaufbau auf NUC/Proxmox ist Debian 13 sinnvoller.

Empfehlung fuer dieses Projekt:

- Neuinstallation: Debian 13 VM
- Bestehende Debian-12-VM: weiter nutzbar, kein Zwangswechsel

## 3. Host-Voraussetzungen (Intel NUC)

Im BIOS aktivieren:

- Intel VT-x
- Intel VT-d (wenn Passthrough gebraucht wird)

Proxmox-Hinweise laut Requirements:

- 64-bit CPU mit VT-x/AMD-V
- SSD empfohlen
- mind. 2 GB fuer Proxmox OS plus RAM fuer Gaeste

Quelle: Proxmox System Requirements (offizielle Produktseite)

## 4. Proxmox Setup (kurz)

1. Proxmox VE installieren (ISO) oder auf Debian aufsetzen.
2. Storage einrichten (lokal SSD/ZFS je nach NUC und RAM).
3. Bridge-Netz (typisch `vmbr0`) konfigurieren.
4. Backup-Storage definieren.

## 5. Gast bereitstellen

### Option A: Debian 13 VM (empfohlen)

Empfohlene Startwerte:

- 2 vCPU
- 2-4 GB RAM
- 16-32 GB Disk (SSD)
- VirtIO NIC

Im Gast:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

Projekt deployen:

```bash
git clone <dein-repo> /opt/cs2tracker
cd /opt/cs2tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # danach Werte setzen
python run.py
```

Dann systemd-Unit aus `docs/OPERATIONS.md` verwenden.

### Option B: Debian LXC

Geht ebenfalls, aber achte auf:

- unprivilegiert bevorzugen
- ausreichend RAM/CPU Limits
- ggf. AppArmor/Nesting nur wenn wirklich noetig

## 6. Konkrete Community Helper Scripts (ProxmoxVE)

Ja, und hier sind konkrete Skripte, die fuer dein Setup sinnvoll sind:

### Host-Tools (`tools/pve`)

- `post-pve-install.sh`: Grundhaertung nach frischer PVE-Installation
- `update-repo.sh`: Repo-Konfiguration aktualisieren
- `update-lxcs.sh`: LXC-Container gesammelt aktualisieren
- `host-backup.sh`: Host-Backup-Helper
- `kernel-clean.sh`: alte Kernel aufraeumen

### VM-Erstellung (`vm`)

- `debian-13-vm.sh`: Debian-13-VM bereitstellen
- `debian-vm.sh`: allgemeine Debian-VM (fallback)
- `docker-vm.sh`: falls du spaeter Container-Workloads kapseln willst

### LXC-Erstellung (`ct`)

- `debian.sh`: Debian-LXC
- `caddy.sh` oder `nginxproxymanager.sh`: Reverse-Proxy als separater Container

## 7. Beispielbefehle fuer Helper Scripts

Nur ausfuehren, wenn du Quelle und Inhalt geprueft hast:

```bash
# Post Install (Host)
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/tools/pve/post-pve-install.sh)"

# Debian 13 VM anlegen
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/vm/debian-13-vm.sh)"

# Debian LXC anlegen
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/debian.sh)"
```

## 8. Netzwerk und Sicherheit

- Kein Direktzugriff aus dem Internet ohne Reverse Proxy + TLS.
- Firewall-Regeln auf Proxmox und Gast setzen.
- Service-User ohne Root-Rechte verwenden.
- `FLASK_DEBUG=0` in Betrieb.
- Starkes `FLASK_SECRET_KEY` setzen.

## 9. Betrieb (Jobs)

Standard ist der interne Scheduler der App (Intervall aus Setup/Settings).
Optional kann Preisaktualisierung zusaetzlich per Cron/systemd timer laufen, z. B. alle 30 Minuten.
Die Telegram-Zusammenfassung (Intervall in Tagen + Versandzeit) laeuft ebenfalls intern ueber den App-Scheduler.

Beispiel Timer fuer `scripts.fetch_all_prices`:

- Service: one-shot Python Aufruf
- Timer: `OnUnitActiveSec=30min`

## 10. Konkrete Empfehlung fuer dich

1. Intel NUC + Proxmox Host sauber installieren.
2. `post-pve-install.sh` fuer Basis-Setup pruefen und nutzen.
3. Debian 13 VM fuer CS2 Tracker anlegen (`debian-13-vm.sh` oder manuell).
4. App als systemd Service betreiben.
5. Proxmox Backup-Job + Snapshot vor Updates.
6. Optional Proxy in separatem LXC (`caddy.sh` oder `nginxproxymanager.sh`).

## 11. Praxiserprobter Migrationsflow (Windows -> Debian 13 VM)

1. Projekt kopieren (vom Windows-Client):

```bash
scp -r "E:\Code\cs2tracker_full_package_arch" <username>@<SERVER-IP>:/home/<username>/
```

2. Venv auf Debian neu erstellen (venv ist nicht plattformportabel):

```bash
cd /home/<username>/cs2tracker_full_package_arch
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. `.env` anlegen:

```bash
cp .env.example .env
```

Empfohlene Werte:

- `FLASK_HOST=0.0.0.0`
- `FLASK_PORT=5000`
- `FLASK_DEBUG=0`

4. Start testen:

```bash
python run.py
ss -ltnp | grep 5000
curl http://127.0.0.1:5000/health
```

5. Service fuer Dauerbetrieb:

```ini
[Unit]
Description=CS2 Tracker
After=network.target

[Service]
User=<username>
WorkingDirectory=/home/<username>/cs2tracker_full_package_arch
EnvironmentFile=/home/<username>/cs2tracker_full_package_arch/.env
ExecStart=/home/<username>/cs2tracker_full_package_arch/.venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cs2tracker
sudo journalctl -u cs2tracker -f
```

Hinweis:

- Flask-Dev-Server ist fuer Homelab/interne Tools ok.
- Fuer haerteren Betrieb: Gunicorn + optional Reverse Proxy einsetzen.

## Quellen

- Proxmox VE Requirements: https://proxmox.com/en/products/proxmox-virtual-environment/requirements
- Community Scripts Repo: https://github.com/community-scripts/ProxmoxVE
- Community Scripts Website: https://community-scripts.github.io/ProxmoxVE/
- PVE Tools Ordner: https://github.com/community-scripts/ProxmoxVE/tree/main/tools/pve
- PVE VM Ordner: https://github.com/community-scripts/ProxmoxVE/tree/main/vm
- PVE CT Ordner: https://github.com/community-scripts/ProxmoxVE/tree/main/ct
