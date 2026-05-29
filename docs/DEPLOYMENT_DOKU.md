# CS2 Tracker – Automatisches Deployment auf Intel NUC

**Datum:** April 2026
**Ziel:** Vollautomatisches Deployment bei jedem `git push origin main` auf den heimischen Intel NUC (Proxmox + Debian VM)

---

## Überblick

Der CS2 Tracker lief seit Februar auf einem Debian-Server auf dem NUC, wurde aber manuell per Datei-Kopieren aktualisiert. Ziel war es, diesen Prozess vollständig zu automatisieren: ein `git push` soll reichen, damit der Server automatisch den neuen Code zieht und den Service neustartet.

---

## Architektur des fertigen Systems

```
Entwicklungsrechner (Windows)
        │
        │  git push origin main
        ▼
    GitHub (wischi2k/cs2tracker)
        │
        │  Webhook → GitHub Actions Workflow
        ▼
Self-Hosted Runner auf NUC (Debian VM 111)
        ├── git pull origin main
        ├── pip install -r requirements.txt
        └── systemctl restart cs2tracker
```

---

## Probleme und Lösungen

### 1. Migration: Alte Installation → Git-basiertes Deployment

**Problem:** Der Server hatte den Code als manuell kopierte Dateien, kein Git-Repository.

**Lösung:**
- Datenbank (`cs2_prices.sqlite`) und `.env` gesichert
- Altes Verzeichnis umbenannt als Backup
- Repository frisch von GitHub geklont
- DB und `.env` wiederhergestellt
- venv neu aufgebaut

---

### 2. GitHub-Authentifizierung: Passwort-Auth abgelaufen

**Problem:** `git clone https://github.com/...` schlug fehl mit „Password authentication is not supported".

**Ursache:** GitHub hat Passwort-Authentifizierung für Git-Operationen abgeschafft.

**Lösung:** SSH-Key auf dem Server erstellt und bei GitHub hinterlegt.

```bash
ssh-keygen -t ed25519 -C "cs2@nuc-debian" -f ~/.ssh/github_cs2tracker -N ""
```

SSH-Config in `~/.ssh/config`:
```
Host github.com
  IdentityFile ~/.ssh/github_cs2tracker
  User git
```

Public Key unter **github.com → Settings → SSH and GPG keys** eingetragen.

---

### 3. Festplatte voll (2,8 GB Partition auf 8 GB Disk)

**Problem:** Die Debian-VM hatte eine 8 GB Disk in Proxmox, aber die Partition war nur 2,8 GB groß. Der GitHub Actions Runner (~1 GB) passte nicht drauf.

**Ursache:** Die Partition wurde bei der VM-Erstellung nicht auf die volle Disk-Größe ausgedehnt.

**Lösung:** Partition online erweitert (kein Reboot nötig):

```bash
sudo apt install -y cloud-guest-utils
sudo growpart /dev/sda 1
sudo resize2fs /dev/sda1
```

Ergebnis: Partition von 2,8 GB auf 7,7 GB gewachsen.

---

### 4. GitHub Actions Runner: Fehlende .NET-Abhängigkeiten

**Problem:** Runner-Installation schlug fehl mit „Libicu's dependencies is missing for Dotnet Core 6.0".

**Lösung:**
```bash
sudo ./bin/installdependencies.sh
```

---

### 5. sudo im Runner funktionierte nicht (Hauptproblem)

**Problem:** Der Workflow-Schritt `sudo systemctl restart cs2tracker` schlug im Runner fehl:
```
sudo: a terminal is required to read the password
sudo: a password is required
```

Obwohl `sudo systemctl restart cs2tracker` in der normalen Shell ohne Passwort funktionierte.

**Ursachenanalyse:**

| Versuch | Problem |
|---|---|
| Sudoers-Datei mit `/bin/systemctl` | Falscher Pfad – Debian nutzt `/usr/bin/systemctl` |
| Dateirechte 644 statt 440 | Sudo ignoriert sudoers.d-Dateien mit falschen Rechten |
| `!requiretty` fehlte | Sudo verweigerte non-interaktive Sessions |
| `use_pty` in globalen Defaults | Sudo erzwang Pseudo-Terminal, das der Runner nicht hat |

**Finale Lösung** – `/etc/sudoers.d/cs2tracker-deploy`:
```
Defaults:cs2 !requiretty
Defaults:cs2 !use_pty
cs2 ALL=(ALL) NOPASSWD: /usr/bin/systemctl
```

Dateirechte korrekt setzen:
```bash
sudo chmod 440 /etc/sudoers.d/cs2tracker-deploy
sudo chown root:root /etc/sudoers.d/cs2tracker-deploy
sudo visudo -c -f /etc/sudoers.d/cs2tracker-deploy
```

---

## Eingerichtete Komponenten

### GitHub Actions Workflow (`.github/workflows/deploy.yml`)

Wird bei jedem Push auf `main` ausgelöst. Läuft auf dem Self-Hosted Runner, zieht den Code, installiert Abhängigkeiten, startet den Service neu.

### Self-Hosted Runner (`~/actions-runner/`)

GitHub Actions Runner als systemd-Service installiert:
```bash
sudo ./svc.sh install cs2
sudo ./svc.sh start
```

Service: `actions.runner.wischi2k-cs2tracker.nuc-debian.service`
Startet automatisch nach Reboot.

### GitHub Repository Variable

`APP_DIR = /home/cs2/cs2tracker_full_package_arch`
Eingestellt unter: Repository → Settings → Secrets and variables → Actions → Variables

---

## Checkliste: Was muss nach einem Server-Neuaufsetzen gemacht werden?

- [ ] SSH-Key neu erstellen und bei GitHub hinterlegen
- [ ] Repository klonen: `git clone git@github.com:wischi2k/cs2tracker.git`
- [ ] `.env` und Datenbank wiederherstellen
- [ ] venv aufbauen: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- [ ] systemd-Service neu anlegen
- [ ] Actions-Runner neu installieren und registrieren (neuer Token von GitHub)
- [ ] sudoers-Datei anlegen (siehe oben)

---

## Nützliche Befehle

```bash
# Service-Status
sudo systemctl status cs2tracker

# Service-Logs live
journalctl -u cs2tracker -f

# Runner-Status
sudo systemctl status actions.runner.wischi2k-cs2tracker.nuc-debian

# Manuell deployen (ohne Push)
cd ~/cs2tracker_full_package_arch
git pull origin main
sudo systemctl restart cs2tracker

# Festplattenplatz prüfen
df -h /
```
