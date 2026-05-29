#!/usr/bin/env bash
# =============================================================================
# migrate_to_git.sh
# Einmalige Migration: Alte CS2-Tracker-Installation → git-basiertes Deployment
#
# Voraussetzungen:
#   - Ausführen als App-Benutzer (z.B. cs2tracker) oder mit sudo
#   - OLD_DIR muss auf das aktuelle Installationsverzeichnis zeigen
#   - NEW_DIR ist der neue Pfad, in dem der Tracker künftig lebt
#
# Sicherheit:
#   - Datenbank und .env werden gesichert und in den neuen Pfad kopiert
#   - Der alte Ordner wird NICHT gelöscht (bleibt als Backup)
# =============================================================================

set -euo pipefail

# ── Konfiguration ─────────────────────────────────────────────────────────────
# ANPASSEN: Pfad zur bestehenden Installation (Ergebnis von "find ... -name run.py")
OLD_DIR="/opt/cs2tracker"          # ← hier deinen gefundenen Pfad eintragen

# Neuer Pfad (hier lebt der Tracker künftig, aus GitHub geklont)
NEW_DIR="/opt/cs2tracker"          # Gleicher Pfad ist in Ordnung — wir machen ein Backup

GITHUB_REPO="https://github.com/wischi2k/cs2tracker.git"
SERVICE_NAME="cs2tracker"
# ──────────────────────────────────────────────────────────────────────────────

echo "=== CS2 Tracker Migration ==="
echo "Alte Installation: $OLD_DIR"
echo "Neuer Pfad:        $NEW_DIR"
echo ""

# 1. Backup der alten Installation
BACKUP_DIR="${OLD_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
echo "[1/7] Erstelle Backup → $BACKUP_DIR"
cp -a "$OLD_DIR" "$BACKUP_DIR"
echo "      ✅ Backup erstellt"

# 2. Datenbank und .env sichern
echo "[2/7] Sichere DB und .env"
DB_FILE=$(find "$OLD_DIR" -name "*.sqlite" -not -name "*test*" | head -1)
ENV_FILE="$OLD_DIR/.env"

if [ -n "$DB_FILE" ]; then
  cp "$DB_FILE" /tmp/cs2tracker_db_backup.sqlite
  echo "      ✅ DB gesichert: $DB_FILE → /tmp/cs2tracker_db_backup.sqlite"
else
  echo "      ⚠️  Keine SQLite-Datenbank gefunden – wird übersprungen"
fi

if [ -f "$ENV_FILE" ]; then
  cp "$ENV_FILE" /tmp/cs2tracker_env_backup
  echo "      ✅ .env gesichert → /tmp/cs2tracker_env_backup"
else
  echo "      ⚠️  Keine .env gefunden – wird übersprungen"
fi

# 3. Service stoppen
echo "[3/7] Stoppe systemd-Service"
sudo systemctl stop "$SERVICE_NAME" || echo "      ℹ️  Service war nicht aktiv"

# 4. Alten Ordner umbenennen, neuen klonen
echo "[4/7] Klone Repository"
TEMP_OLD="${OLD_DIR}_old_$(date +%s)"
mv "$OLD_DIR" "$TEMP_OLD"
git clone "$GITHUB_REPO" "$NEW_DIR"
echo "      ✅ Geklont nach $NEW_DIR"

# 5. DB und .env wiederherstellen
echo "[5/7] Stelle DB und .env wieder her"
if [ -f /tmp/cs2tracker_db_backup.sqlite ]; then
  DB_NAME=$(basename "$DB_FILE")
  cp /tmp/cs2tracker_db_backup.sqlite "$NEW_DIR/$DB_NAME"
  echo "      ✅ DB wiederhergestellt: $NEW_DIR/$DB_NAME"
fi

if [ -f /tmp/cs2tracker_env_backup ]; then
  cp /tmp/cs2tracker_env_backup "$NEW_DIR/.env"
  echo "      ✅ .env wiederhergestellt"
fi

# 6. Virtualenv und Abhängigkeiten
echo "[6/7] Erstelle venv und installiere Abhängigkeiten"
cd "$NEW_DIR"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt --quiet
echo "      ✅ Abhängigkeiten installiert"

# 7. Service starten
echo "[7/7] Starte Service neu"
sudo systemctl start "$SERVICE_NAME"
sleep 3
sudo systemctl is-active --quiet "$SERVICE_NAME" \
  && echo "      ✅ $SERVICE_NAME läuft" \
  || echo "      ❌ Service-Start fehlgeschlagen — prüfe: journalctl -u $SERVICE_NAME -n 30"

echo ""
echo "=== Migration abgeschlossen ==="
echo "Neuer Installationspfad: $NEW_DIR"
echo "Backup liegt unter:      $TEMP_OLD"
echo ""
echo "Nächster Schritt: GitHub Actions Runner einrichten (siehe docs/OPERATIONS.md)"
