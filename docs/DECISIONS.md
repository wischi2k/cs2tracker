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

## 010 - Brutto vs. Netto Schwellenwert je Item-Typ

- Status: umgesetzt
- Kontext: Beim Verkauf (Inventar) verliert man 15 % Fee — relevant ist der Netto-Preis. Beim Kauf (Tracking) zahlt man den vollen Brutto-Preis.
- Entscheidung: Inventar-Alerts auf Netto-Preis, Tracking-Alerts auf Brutto-Preis. Standardrichtung: Inventar = Überschreitung (≥), Tracking = Unterschreitung (≤). Beides manuell anpassbar.
- Konsequenz: Natürlichere UX — Zahlen in der App entsprechen dem was der Nutzer tatsächlich zahlt oder erhält.
