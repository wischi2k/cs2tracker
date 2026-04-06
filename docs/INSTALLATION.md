# CS2 Tracker — Installationsanleitung für Einsteiger

Diese Anleitung erklärt Schritt für Schritt, wie du CS2 Tracker auf deinem eigenen Computer zum Laufen bringst. Keine Vorkenntnisse nötig.

---

## Was du brauchst

- Einen Computer mit **Windows 10/11**, **macOS** oder **Linux** (Ubuntu/Debian)
- Eine aktive Internetverbindung
- Ca. 15 Minuten Zeit

---

## Schritt 1 — Python installieren

CS2 Tracker läuft mit Python. Prüfe zuerst, ob Python bereits installiert ist.

### Windows

1. Drücke `Win + R`, tippe `cmd`, drücke Enter → ein schwarzes Fenster öffnet sich (das **Terminal**)
2. Tippe ein und drücke Enter:
   ```
   python --version
   ```
3. Wenn du `Python 3.10.x` oder neuer siehst → weiter zu Schritt 2
4. Wenn du eine Fehlermeldung bekommst: Python herunterladen von **python.org** → Installer ausführen
   - **Wichtig:** Haken bei **„Add Python to PATH"** setzen, bevor du auf „Install Now" klickst

### macOS

1. Öffne das Terminal (Spotlight: `Cmd + Leertaste` → `Terminal` eintippen)
2. Tippe ein:
   ```
   python3 --version
   ```
3. Wenn Python fehlt, öffnet macOS automatisch einen Dialog zur Installation — dem folgen

### Linux (Ubuntu / Debian)

Python 3 ist auf den meisten Linux-Systemen bereits vorinstalliert. Prüfen und ggf. installieren:

```bash
python3 --version
```

Falls die Version fehlt oder zu alt ist (unter 3.10):

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

> **Hinweis `python3-venv`:** Auf Ubuntu/Debian ist das venv-Modul manchmal nicht im Python-Paket enthalten. Falls Schritt 4 mit einem Fehler abbricht, einfach `sudo apt install python3-venv` ausführen.

---

## Schritt 2 — Code herunterladen

### Option A: Als ZIP (einfachster Weg, kein Git nötig)

1. Gehe zu: **github.com/wischi2k/cs2tracker**
2. Klicke auf den grünen Button **„Code"** → **„Download ZIP"**
3. Entpacke die ZIP-Datei an einen Ort deiner Wahl, z. B.:
   - Windows: `C:\cs2tracker\`
   - macOS/Linux: `~/cs2tracker/`

### Option B: Mit Git (für regelmäßige Updates empfohlen)

Falls Git installiert ist (Linux: `sudo apt install git`):

```bash
git clone https://github.com/wischi2k/cs2tracker.git
```

---

## Schritt 3 — Terminal im Projektordner öffnen

Du musst im Terminal in den Ordner navigieren, in den du den Code entpackt hast.

### Windows

**Methode (einfach):** Öffne den Ordner im Explorer → in die Adressleiste klicken → `cmd` eintippen → Enter drücken

Oder manuell im Terminal:
```
cd C:\cs2tracker\cs2tracker-main
```
*(Passe den Pfad an deinen Entpack-Ort an)*

### macOS

```bash
cd ~/cs2tracker/cs2tracker-main
```

### Linux

Terminal öffnen: `Strg + Alt + T` (Ubuntu/Debian mit Desktop) oder direkt aus dem Dateimanager heraus.

```bash
cd ~/cs2tracker/cs2tracker-main
```

---

## Schritt 4 — Virtuelle Umgebung erstellen

Eine „virtuelle Umgebung" ist ein isolierter Bereich für die Abhängigkeiten des Projekts — sie beeinflusst nicht dein restliches System.

```bash
# Windows
python -m venv .venv

# macOS / Linux
python3 -m venv .venv
```

Danach die Umgebung aktivieren:

```bash
# Windows (CMD)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Du erkennst, dass es geklappt hat, wenn am Anfang der Zeile `(.venv)` steht.

> **PowerShell-Fehler (Windows)?** Falls Windows meldet „Ausführen von Skripts wurde deaktiviert", einmalig ausführen:
> ```
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

> **Linux-Fehler `ensurepip`?** Falls die Fehlermeldung `Error: package 'python3-venv' not found` erscheint:
> ```bash
> sudo apt install python3-venv
> ```
> Dann Schritt 4 erneut ausführen.

---

## Schritt 5 — Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Das lädt alle benötigten Bibliotheken herunter. Das kann 1–2 Minuten dauern.

> **Linux-Hinweis:** Falls `pip` nicht gefunden wird, `pip3` verwenden oder sicherstellen, dass die virtuelle Umgebung aktiv ist (`.venv` muss am Anfang der Zeile stehen).

---

## Schritt 6 — App starten

```bash
# Windows
python run.py

# macOS / Linux
python3 run.py
```

Wenn alles klappt, siehst du etwas wie:
```
 * Running on http://127.0.0.1:5000
```

**Lass das Fenster offen** — sobald du es schließt, stoppt die App.

---

## Schritt 7 — Browser öffnen und Setup durchführen

1. Öffne deinen Browser (Chrome, Firefox, Edge …)
2. Gib in die Adresszeile ein: **`http://127.0.0.1:5000`**
3. Du wirst automatisch zum **Setup-Assistenten** weitergeleitet

### Setup-Assistent — Was muss ich eingeben?

| Feld | Was es bedeutet | Empfehlung |
|---|---|---|
| **Preisupdate-Intervall** | Wie oft (in Minuten) soll der aktuelle Preis von Steam abgerufen werden? | 30 Minuten |
| **Zugriff auf Web-UI** | Von wo soll die App erreichbar sein? | „Lokales Netzwerk" wenn du vom Handy/anderem PC zugreifen willst, sonst „Nur lokal" |
| **Design / Theme** | Farb-Design der Oberfläche | Beliebig — jederzeit änderbar |
| **Telegram** | Optional: Bot für Preisalarme per Telegram | Kann übersprungen werden |

4. Klicke auf **„Setup abschließen"** → du kommst zum Dashboard

---

## Schritt 8 — Ersten Skin hinzufügen

1. Klicke auf **„+ Hinzufügen"**
2. Gehe auf **store.steampowered.com/market** und suche deinen Skin
3. Kopiere die **URL der Seite** aus der Adressleiste des Browsers, z. B.:
   ```
   https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20%28Field-Tested%29
   ```
4. Füge sie in das Feld **„Steam-Market-URL"** ein
5. Trage optional deinen **Kaufpreis** ein (z. B. `6,50`)
6. Klicke **„Hinzufügen"** — der aktuelle Preis wird sofort abgerufen

---

## App beenden und neu starten

**Beenden:** Im Terminal `Strg + C` drücken

**Neu starten:** Schritte 3 → 4 (Umgebung aktivieren) → Schritt 6 wiederholen

> Tipp: Lege dir eine Schnellstart-Datei an, die alle Schritte auf einmal ausführt — siehe unten.

### Windows — Schnellstart-Datei erstellen

Erstelle eine Datei namens `start.bat` im Projektordner mit folgendem Inhalt:

```bat
@echo off
cd /d %~dp0
call .venv\Scripts\activate.bat
python run.py
pause
```

Doppelklick auf `start.bat` → App startet.

### macOS / Linux — Schnellstart-Skript erstellen

Erstelle eine Datei `start.sh` im Projektordner:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python3 run.py
```

Einmalig ausführbar machen:
```bash
chmod +x start.sh
```

Danach mit `./start.sh` starten. Auf macOS auch per Doppelklick möglich (Rechtsklick → Öffnen mit → Terminal).

---

## Häufige Fehler

### „python" wird nicht erkannt / `python` ist nicht vorhanden

- **Windows:** Python wurde ohne „Add to PATH" installiert → Python deinstallieren und neu installieren, diesmal Haken setzen
- **macOS / Linux:** `python3` statt `python` verwenden

---

### Port bereits belegt: `Address already in use`

Ein anderes Programm nutzt Port 5000. Entweder:
- Das andere Programm beenden
- Oder in der `.env`-Datei einen anderen Port setzen (z. B. `FLASK_PORT=5001`)

---

### `.venv\Scripts\Activate.ps1` kann nicht ausgeführt werden (Windows PowerShell)

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### `python3-venv` fehlt (Linux)

```bash
sudo apt install python3-venv
```

Danach die virtuelle Umgebung neu erstellen (Schritt 4).

---

### Pip-Fehler: `No module named pip`

```bash
# Windows
python -m ensurepip --upgrade

# macOS / Linux
python3 -m ensurepip --upgrade
```

---

### Steam-Preis kann nicht abgerufen werden

Steam hat gelegentlich Rate-Limits. Warte ein paar Minuten und klicke auf **„Preis aktualisieren"** in der Detailansicht des Items.

---

## Optionale Konfiguration via `.env`

Für erweiterte Einstellungen kannst du im Projektordner eine Datei namens `.env` anlegen (Vorlage: `.env.example`):

```env
FLASK_HOST=0.0.0.0      # 0.0.0.0 = im Heimnetz erreichbar; 127.0.0.1 = nur dieser PC
FLASK_PORT=5000
FLASK_DEBUG=false
CS2_DB_PATH=cs2_prices.sqlite
CS2_SECRET_KEY=ein-langes-zufaelliges-passwort
```

> **CS2_SECRET_KEY:** Eine beliebige lange Zeichenkette (z. B. `meinGeheimesPasswort1234`). Wird zur Verschlüsselung von Telegram-Zugangsdaten genutzt. Nach dem ersten Start nicht mehr ändern, sonst werden gespeicherte Secrets unleserlich.

---

## App dauerhaft laufen lassen (ohne Terminal offen halten)

Wenn du die App dauerhaft im Hintergrund laufen lassen möchtest:

- **Linux (Ubuntu/Debian, Heimserver):** `docs/OPERATIONS.md` → Abschnitt „Betrieb mit systemd"
- **Intel NUC + Proxmox:** `docs/DEPLOY_INTEL_NUC_PROXMOX.md`
- **Windows:** Task-Scheduler oder die `start.bat` beim Windows-Start ausführen lassen

---

## Einstellungen ändern

Alle Einstellungen aus dem Setup sind jederzeit unter **`http://127.0.0.1:5000/settings`** änderbar:

- Update-Intervall
- Theme
- Telegram-Bot-Token und Chat-ID
- Telegram-Zusammenfassungs-Zeitplan
