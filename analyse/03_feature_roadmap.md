# Feature-Roadmap — Vorschläge für sinnvolle Erweiterungen

Stand: 2026-07-31 · Priorisiert nach Nutzwert für den realen Anwendungsfall (privates Portfolio, self-hosted, Telegram-first). Die Vorschläge bauen teils aufeinander auf.

## Stufe 1 — Kernlücken im Portfolio-Modell (höchster Nutzwert)

### 1.1 Stückzahl (Quantity) pro Item ⭐ wichtigste Einzelerweiterung

Aktuell muss jedes Exemplar als eigenes Item angelegt werden. Wer 20 gleiche Kisten hält (der häufigste CS2-Investment-Fall!), legt 20 Einträge an — oder trackt falsch. Alle kommerziellen Tracker haben Mengen-Support.

- Schema: `quantity INTEGER DEFAULT 1` auf `items`, Kaufpreis als Durchschnittspreis interpretieren
- Portfolio-Summe, Summary und KPI-Cards multiplizieren mit Menge
- Nebeneffekt: weniger Steam-Requests (1 statt 20 für identische Items)
- Aufwand: 1–2 Abende

### 1.2 Verkaufs-Workflow (realisierter Gewinn)

Es gibt „Gekauft" (promote), aber kein „Verkauft". Löschen vernichtet die Historie, und realisierter Gewinn ist nicht abbildbar — dabei ist „Wie viel habe ich insgesamt verdient?" *die* Portfolio-Frage.

- `sold_at`, `sold_price_cents` auf `items`; verkaufte Items aus dem aktiven Portfolio raus, in eine „Verkauft"-Ansicht rein
- Neue KPI: realisierter G/V gesamt + pro Item; Summary-Abschnitt „Verkäufe im Zeitraum"
- Ersetzt das gefährliche harte Löschen im Alltag
- Aufwand: 2–3 Abende

### 1.3 Portfolio-Verlaufschart

Es gibt Preisverläufe pro Item, aber keinen Gesamtwert-Verlauf — das Herzstück jeder kommerziellen Portfolio-Ansicht („dein Depot über Zeit").

- Neue Tabelle `portfolio_snapshots(ts, total_gross_cents, total_net_cents, total_buy_cents)`; der Scheduler schreibt nach jedem Preislauf einen Snapshot
- Chart auf dem Dashboard über dem KPI-Streifen; 24h/7d/30d-Badges fallen als Nebenprodukt ab
- Aufwand: 1–2 Abende (Snapshots ab sofort; Rückrechnung aus `prices` optional)

## Stufe 2 — Komfort & Datenqualität

### 2.4 Steam-Inventar-Import

Killer-Feature aller kommerziellen Tools: SteamID64 eingeben, Inventar wird eingelesen (`steamcommunity.com/inventory/<id>/730/2`, bei öffentlichem Inventar ohne Login). Vorschau mit Checkboxen → ausgewählte Items als Portfolio-Items anlegen (Kaufpreise manuell nachtragen). Achtung: Endpoint ist aggressiv rate-limitiert → mit Delay und Cache arbeiten. Aufwand: 2–3 Abende.

### 2.5 CSV-Export (und -Import)

Export von Items + Historie für Excel/Steuer/Backup; Import als Bulk-Anlage (`name;url;buy;qty`). Passt zur Self-Hosted-Philosophie („deine Daten gehören dir"). Aufwand: 1 Abend.

### 2.6 Alert-Ausbau

Aktuell: einmaliger Schwellwert-Alert, löscht sich selbst. Sinnvoll:

- **Prozent-Alerts** („±10 % in 24h") — nützlicher als absolute Schwellen bei volatilen Items
- **Wiederkehrende Alerts** (Re-Arm nach Abkühlphase statt Selbstlöschung)
- Portfolio-Level-Alert („Gesamtwert unter/über X")
- Aufwand: je Punkt wenige Stunden

### 2.7 Backup über die UI

SQLite-Datei per Knopfdruck herunterladen (`VACUUM INTO`), optional zeitgesteuertes Backup auf ein Zielverzeichnis. Für ein Geld-Tracking-Tool auf einem NUC fast schon Pflicht. Aufwand: wenige Stunden.

## Stufe 3 — Ausbau Richtung „kleiner Pricempire"

### 3.8 Zweite Preisquelle: Skinport

Die [Skinport-API](https://docs.skinport.com) (`/v1/items`) ist öffentlich, kostenlos und liefert alle Preise in einem einzigen Request — ideal als Zweitquelle neben Steam (Steam-Preis ≠ realer Verkaufspreis auf Drittmärkten, Skinport-Fee 12 % statt 15 %). Anzeige als zweite Linie im Chart / zweite Spalte in der Card. Aufwand: 2 Abende. *(Buff163/CSFloat haben keine offenen APIs — bewusst weglassen.)*

### 3.9 Währungs-/Kursoption

EUR ist hartkodiert (`currency=3`). Konfigurierbare Währung + optional EZB-Kurse für Umrechnung. Nur sinnvoll, wenn tatsächlich Bedarf besteht. Aufwand: 1 Abend.

### 3.10 Mehr-Nutzer / Auth

Aktuell schützt nur der Netzwerk-Scope. Ein einfacher Login (eine Passwort-Hürde, Flask-Login) würde LAN-Betrieb absichern und Remote-Zugriff (VPN/Reverse-Proxy) ermöglichen. Voraussetzung für alles Weitere in diese Richtung. Aufwand: 1–2 Abende.

## Bewusst NICHT empfohlen

- **Float-Werte/Pattern/Stickers-Aufpreise tracken** — dafür braucht es Inspect-Link-Infrastruktur (CSFloat-API o. ä.); hoher Aufwand, Nische, kommerzielle Tools machen das besser.
- **30-Marktplatz-Aggregation** — Konkurrenz zu Pricempire ist nicht die Nische dieses Tools; die APIs sind fast alle kostenpflichtig.
- **Umbau zu SPA (React/Vue)** — die Server-Rendered-Architektur ist ein Feature (einfach, wartbar, self-hosted); htmx reicht (siehe UI-Dokument).
- **Trading-/Kauf-Automation** — ToS-Risiko bei Steam, Account-Bann möglich.

## Empfohlene Reihenfolge (Quartalssicht)

1. Technische Basis aus Dokument 01 (CSRF, Index, Tests) — 1 Woche nebenbei
2. Quantity (1.1) + Verkaufs-Workflow (1.2) — das Portfolio-Modell wird „richtig"
3. Portfolio-Chart (1.3) + Mobile-Layout (aus Dokument 02) — das Tool wird täglich-nutzbar
4. Danach nach Lust: Inventar-Import (2.4) oder Skinport (3.8)
