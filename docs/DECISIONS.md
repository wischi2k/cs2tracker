# Entscheidungen (ADR-light)

## 001 - Schichtenarchitektur statt Monolith

- Status: umgesetzt
- Kontext: `app.py` enthielt Route-, DB- und Integrationslogik gemischt.
- Entscheidung: Trennung in `web/services/repositories/infrastructure/domain`.
- Konsequenz: Mehr Dateien, aber klarere Verantwortlichkeiten und bessere Testbarkeit.

## 002 - SQLite bleibt vorerst Default

- Status: umgesetzt
- Kontext: Ein-Host-Deployment, geringe operative Komplexitaet gewuenscht.
- Entscheidung: SQLite weiterhin als Standard.
- Konsequenz: Einfaches Backup, wenig Betriebsaufwand; bei hohem Parallelismus spaeter PostgreSQL pruefen.

## 003 - Kompatible Endpoint-Namen

- Status: umgesetzt
- Kontext: Templates referenzieren bestehende `url_for()` Endpoints.
- Entscheidung: Alte Endpoint-Namen beibehalten und in neuer Routenstruktur registrieren.
- Konsequenz: Migration ohne Frontend-Neubau moeglich.

## 004 - Defensives Verhalten bei externen APIs

- Status: umgesetzt
- Kontext: Steam/Telegram koennen timeouten oder Fehler liefern.
- Entscheidung: Clients geben kontrollierte Fehlerwerte zurueck, keine unkontrollierten Exceptions in User-Flows.
- Konsequenz: Hoehere Stabilitaet, aber Fehler muessen sauber geloggt werden.

## 005 - App-Factory + explizites Wiring

- Status: umgesetzt
- Kontext: Initialisierung war implizit verteilt.
- Entscheidung: `create_app()` als Einstieg und zentrale Komposition.
- Konsequenz: Einheitlicher Startpunkt fuer Tests und Deployments.

## 006 - Browserbasiertes Setup als eigene Schicht

- Status: umgesetzt
- Kontext: Setup-Logik wurde zuvor monolithisch in die Haupt-App gemischt.
- Entscheidung: Setup in `routes_setup` + `SetupService` + `ConfigRepository` modular integrieren.
- Konsequenz: Gleiche Funktionalitaet wie vorher, aber sauber im Architekturmodell verankert.

## 007 - Telegram-Secrets in SQLite verschluesselt

- Status: umgesetzt
- Kontext: Bot-Token/Chat-ID sollten nicht im Klartext in Templates oder Logs landen.
- Entscheidung: Speicherung in `secret_store` mit stream-XOR ueber aus Secret-Key abgeleitetes Material.
- Konsequenz: Besserer Basisschutz bei gleichbleibend einfacher Deployment-Komplexitaet.

## 008 - Tracking-Feature: zwei Item-Typen statt separater Tabelle

- Status: umgesetzt
- Kontext: Neue Anforderung, auch noch nicht gekaufte Items zu tracken und bei Preisunterschreitung zu benachrichtigen.
- Entscheidung: Kein separates Schema. Stattdessen `item_type TEXT ('inventory'|'tracking')` in der bestehenden `items`-Tabelle. Gleiche Preis-Historisierung, gleicher Scheduler.
- Konsequenz: Minimale Migrationskosten, alle bestehenden Items werden automatisch als `inventory` klassifiziert.

## 009 - Alert einmalig auslösen, triggered_at persistieren

- Status: umgesetzt
- Kontext: Wiederholte Alerts bei jedem Preisfetch wuerden Telegram-Spam erzeugen.
- Entscheidung: Alert feuert einmalig. `threshold_net_eur` wird auf NULL gesetzt, `triggered_at` bleibt erhalten.
- Konsequenz: Kein Spam. Auslösezeitpunkt ist im Chart als vertikale Linie sichtbar.

## 011 - 3-Sekunden-Delay zwischen Steam-API-Requests

- Status: umgesetzt
- Kontext: Steam hat das Rate-Limiting der `priceoverview`-API verschaerft (HTTP 429, Body `null`). Beim Bulk-Refresh aller Items wurden Anfragen ohne Pause gesendet, was zur Folge hatte, dass fast alle Preise mit `None` zurueckkamen.
- Entscheidung: In `refresh_all_active_prices()` wird zwischen jedem Request `time.sleep(3)` eingefuegt. Ausserdem wird HTTP 429 in `fetch_price_cents()` explizit abgefangen und `isinstance(data, dict)` geprueft, damit ein `null`-Body keine Exception mehr wirft.
- Konsequenz: Ein Bulk-Refresh mit n Items dauert ca. n×3 Sekunden. Bei den typischen 5–30 Items (15–90 s) ist das akzeptabel, da Live-Preise keine Anforderung sind.

## 010 - Brutto vs. Netto Schwellenwert je Item-Typ

- Status: umgesetzt
- Kontext: Beim Verkauf (Inventar) verliert man 15 % Fee — relevant ist der Netto-Preis. Beim Kauf (Tracking) zahlt man den vollen Brutto-Preis.
- Entscheidung: Inventar-Alerts auf Netto-Preis, Tracking-Alerts auf Brutto-Preis. Standardrichtung: Inventar = Überschreitung (≥), Tracking = Unterschreitung (≤). Beides manuell anpassbar.
- Konsequenz: Natürlichere UX — Zahlen in der App entsprechen dem was der Nutzer tatsächlich zahlt oder erhält.

## 012 - CSRF-Schutz über Flask-WTF

- Status: umgesetzt
- Kontext: Alle POST-Endpunkte (Löschen, Alerts, Settings) waren ohne CSRF-Token. Da die App per `ui_access_scope=private_network` bewusst im LAN erreichbar ist, konnte jede im Browser geöffnete Webseite state-ändernde Requests auslösen (z. B. Items löschen).
- Entscheidung: `CSRFProtect(app)` in `create_app()` aktiviert (Flask-WTF). Alle 14 POST-Formulare in den aktiven Templates tragen ein `csrf_token`-Hidden-Field. POSTs ohne gültiges Token werden mit HTTP 400 abgelehnt.
- Konsequenz: Eine neue Dependency (`flask-wtf`). Externe POSTs ohne Session-Token sind nicht mehr möglich; eigene Skripte gegen die App müssten das Token mitschicken oder per `csrf.exempt` freigeschaltet werden.

## 013 - Index auf prices(item_id, ts) + WAL-Journal-Mode

- Status: umgesetzt
- Kontext: Die `prices`-Tabelle wächst mit jedem Scheduler-Lauf (Snapshots pro Item). Die korrelierte Subquery „letzter Preis pro Item" sowie Chart- und Summary-Abfragen mussten ohne Index die gesamte Historie scannen — mit wachsender Laufzeit über Monate spürbar. Zusätzlich konkurrieren Scheduler-Thread und Web-Requests um dieselbe SQLite-Datei.
- Entscheidung: `CREATE INDEX IF NOT EXISTS idx_prices_item_ts ON prices(item_id, ts DESC)` in `ensure_schema()` (greift automatisch beim nächsten Start, auch für Bestands-DBs). `PRAGMA journal_mode=WAL` in `get_connection()` für bessere Lese-/Schreib-Parallelität und weniger `database is locked`-Risiko.
- Konsequenz: Latest-Price-, Chart- und Summary-Queries nutzen den Index (O(log n) statt Scan). WAL erzeugt `-wal`/`-shm`-Begleitdateien neben der DB (bereits in `.gitignore`); Backups müssen die DB per `VACUUM INTO` oder nach einem Checkpoint sichern, nicht per rohem Datei-Copy während des Betriebs.

## 014 - Stückzahl (quantity) statt Item-Duplikate

- Status: umgesetzt
- Kontext: Mehrere Exemplare desselben Items (typisch: Kisten-Investments) mussten als einzelne Zeilen angelegt werden — verfälschte Portfolio-Summen oder n-fache Steam-Requests für identische Preise.
- Entscheidung: `quantity INTEGER NOT NULL DEFAULT 1` auf `items`. Kaufpreis wird als Durchschnittspreis pro Stück interpretiert. Alle Preisanzeigen (Card, Detail, Chart) bleiben pro Stück; Portfolio-Summen, Snapshots und Telegram-Summary rechnen Preis × Stückzahl. Alerts bleiben pro Stück.
- Konsequenz: Ein Steam-Request pro Item unabhängig von der Menge. Bestehende Items bekommen automatisch `quantity=1` — keine Verhaltensänderung ohne Zutun.

## 015 - Portfolio-Snapshots als eigene Zeitreihe

- Status: umgesetzt
- Kontext: Es gab Preisverläufe pro Item, aber keinen Gesamtwert-Verlauf. Nachträgliche Berechnung aus `prices` wäre bei jedem Dashboard-Aufruf teuer und würde historische Bestandsänderungen (Item hinzugefügt/entfernt) falsch abbilden.
- Entscheidung: Tabelle `portfolio_snapshots(ts, total_gross_cents, total_net_cents, total_buy_cents, item_count)`. Der Scheduler schreibt nach jedem erfolgreichen Preislauf einen qty-gewichteten Snapshot über aktive Inventar-Items (Tracking-Items zählen nicht). Dashboard rendert die Zeitreihe mit Zeitraum-Schaltern (7T/30T/90T/Alles) clientseitig gefiltert.
- Konsequenz: Ein Snapshot pro Preislauf (bei 30-Min-Intervall ~48 Zeilen/Tag — vernachlässigbar). Die Kurve beginnt ab Einführung; keine Rückrechnung.

## 016 - Steam-Inventar-Import als idempotenter Abgleich

- Status: umgesetzt
- Kontext: Items einzeln per Market-URL anzulegen ist der größte Reibungspunkt beim Onboarding. Zusätzlich gewünscht: konfigurierbar, welche Inventar-Items getrackt werden.
- Entscheidung: `/import` lädt das öffentliche CS2-Inventar (SteamID64, Profil-URL oder Vanity-Name; Endpoint `steamcommunity.com/inventory/<id>/730/2`, nur marketable Items, aggregiert nach `market_hash_name`). Die Seite ist ein Abgleich, kein Einmal-Import: Checkbox an = tracken (neu anlegen oder reaktivieren), Checkbox aus = deaktivieren (`is_active=0`, Historie bleibt). Stückzahlen werden auf den Inventar-Stand aktualisiert. Neue Items starten ohne Kaufpreis; Preise lädt der Scheduler im Hintergrund (Trigger: `auto_refresh_last_run_ts=0`).
- Konsequenz: Wiederholbarer Abgleich statt Duplikate; kein Löschen von Historie über den Import. Privates Inventar oder Steam-429 wird mit verständlicher Fehlermeldung abgefangen. Import-Endpunkte sind wie Setup/Settings auf lokale/private Netze beschränkt.

## 017 - Globaler Steam-Lock, Cooldown und Inventory-Preview-Cache

- Status: umgesetzt
- Kontext: Der Inventory-Endpoint und die Market-Preis-API werden von Steam aggressiv limitiert. Der Import selbst laedt zwar seriell, konnte aber parallel zu einem Scheduler-Preisrefresh laufen. Wiederholte Klicks auf "Inventar laden" haben nach einem 429 sofort weitere Steam-Requests ausgeloest.
- Entscheidung: Alle groesseren Steam-Zugriffe teilen sich `steam_request_lock_until_ts` in `app_config`. Bei HTTP 429 wird `steam_rate_limit_until_ts` fuer 15 Minuten gesetzt. Der Scheduler startet waehrend des Cooldowns keinen Preisrefresh und bricht einen laufenden Refresh beim ersten 429 ab. Erfolgreiche Inventory-Previews werden 15 Minuten in `steam_inventory_preview_cache_json` gespeichert.
- Konsequenz: Weniger konkurrierende Steam-Requests und kein lokales Nachfeuern waehrend eines Rate-Limits. Der Import kann direkt erneut angezeigt werden, solange der lokale Preview-Cache gueltig ist. Nach einem echten 429 muss der Nutzer warten, bekommt aber eine klare Restzeit statt einer generischen Fehlermeldung.

## 018 - Curl-Fallback fuer Steam-Inventar-Import

- Status: umgesetzt
- Kontext: Auf dem CS2-Tracker-Server lieferte der direkte Inventory-Endpunkt per `curl` HTTP 200 mit Inventar-JSON, waehrend Python `requests` und `urllib` fuer dieselbe URL HTTP 429 mit Body `null` bekamen. Das Inventar war oeffentlich sichtbar; das Problem lag am Python-HTTP-Abruf/Fingerprint, nicht am Profil-Link.
- Entscheidung: `SteamClient.fetch_inventory()` versucht den normalen Python-Request weiterhin zuerst. Wenn Steam darauf HTTP 429 liefert oder die Antwort kein JSON-Dict ist, ruft der Client dieselbe URL per lokalem `curl -fsS --compressed --max-time 25` ab und parsed das JSON danach mit derselben Aggregationslogik.
- Konsequenz: Der Import bleibt fuer Nutzer automatisch und nutzt den auf dem Server nachweislich funktionierenden HTTP-Client. `curl` wird damit zur Runtime-Voraussetzung fuer den robusten Inventar-Import. Preisabrufe bleiben unveraendert bei Python `requests`, damit nicht jeder Scheduler-Lauf Shell-Prozesse startet.
