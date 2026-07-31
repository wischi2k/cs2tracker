# Projekt-Analyse: CS2 Tracker

Analyse-Datum: 2026-07-31 · Analysierter Stand: Commit `8752b15` (main)

## Dokumente

| Dokument | Inhalt |
|---|---|
| [01_technische_bewertung.md](01_technische_bewertung.md) | Architektur, Code-Qualität, Sicherheit, Performance, Repo-Hygiene |
| [02_ui_ux_bewertung.md](02_ui_ux_bewertung.md) | Optische Bewertung, UX-Schwächen, konkrete Verbesserungen |
| [03_feature_roadmap.md](03_feature_roadmap.md) | Priorisierte Feature-Vorschläge mit Aufwandsschätzung |
| [04_marktvergleich.md](04_marktvergleich.md) | Vergleich mit Pricempire, CSGOSKINS.GG, Skinpock, CSGAIN u. a. |

## Gesamtbewertung (Kurzfassung)

**Note: gut bis sehr gut für ein Self-Hosted-Hobbyprojekt — mit klaren, benennbaren Lücken.**

### Was überzeugt

- **Architektur:** Saubere Schichtentrennung (Routes → Services → Repositories → Infrastructure) mit Dependency Injection in `create_app()`. Für die Projektgröße vorbildlich, nicht überengineert.
- **Dokumentation:** `docs/` mit Entscheidungslog, Architektur-, Betriebs- und Deploy-Doku ist weit über Hobby-Niveau.
- **Betriebsreife:** Scheduler mit SQLite-Lock gegen Doppelläufe, `/health`-Endpoint, Zugriffs-Scope (lokal/LAN), verschlüsselte Telegram-Secrets, Rate-Limit-Schutz (3s-Delay).
- **Design-System:** 4 konsistente Themes über CSS Custom Properties, durchdachte Variablen-Hierarchie.

### Die fünf wichtigsten Baustellen

1. **Keine Tests** — kein einziger automatisierter Test im Projekt. Größtes Einzelrisiko bei Weiterentwicklung.
2. **Kein CSRF-Schutz** — alle POST-Formulare (inkl. Löschen) sind bei LAN-Scope ungeschützt gegen Cross-Site-Request-Forgery.
3. **Fehlende DB-Indizes** — `prices(item_id, ts)` hat keinen Index; jede Preisabfrage scannt die wachsende Historie.
4. **Kein Logging** — Fehler werden per `except Exception` verschluckt; Diagnose im Fehlerfall kaum möglich.
5. **Kein Mobile-Layout** — das feste Zwei-Spalten-Grid bricht auf Smartphones; genau dort schaut man aber „mal eben Preise nach".

### Strategische Einordnung

Gegen kommerzielle Tracker (Pricempire & Co.) gewinnt das Projekt nicht über Datenbreite — die aggregieren 30–40 Marktplätze. Die realistische Nische ist: **self-hosted, privat, werbefrei, Telegram-first**. Die Roadmap in Dokument 03 ist auf diese Nische ausgerichtet; wichtigste Empfehlungen dort: Stückzahl-Support, Verkaufs-Workflow (realisierter Gewinn), Steam-Inventar-Import und ein Portfolio-Verlaufschart.
