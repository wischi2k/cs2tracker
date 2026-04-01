# Architektur

## Ziel

Die Anwendung ist in Schichten getrennt, damit Aenderungen lokal bleiben und Tests einfacher werden.

## Schichten

- `app/web`: HTTP-Routen, Request/Response, Rendering
- `app/services`: Business-Logik und Use-Cases
- `app/repositories`: SQL-Zugriffe und Persistenzdetails
- `app/infrastructure`: Externe Schnittstellen (Steam, Telegram, Secret-Crypto)
- `app/domain`: Interne Datenmodelle fuer die App

## Laufzeitfluss (Beispiel `/item/<id>`)

1. Route in `app/web/routes_items.py` empfaengt Request.
2. `ItemService` liefert View-Daten und Chart-Payload.
3. `ItemRepository` liest Daten aus SQLite.
4. Route rendert Template mit den aufbereiteten Daten.

## Laufzeitfluss (Beispiel `/setup`)

1. `routes_setup` prueft Zugriff (lokal/privat) und Setup-Status.
2. `SetupService` liest/schreibt Setup-Werte.
3. `ConfigRepository` persistiert `app_config` und `secret_store`.
4. `TelegramClient` testet Versand optional mit Formularwerten.

## Inversion of Control

Wiring passiert zentral in `app/__init__.py`:

- `ItemRepository`
- `ConfigRepository`
- `SteamClient`
- `TelegramClient`
- `ItemService`
- `SetupService`
- Route-Registrierung

Damit sind Abhaengigkeiten explizit und austauschbar.

## Datenbank

- Datei: per `CS2_DB_PATH`, default `cs2_prices.sqlite`
- Connection: `app/db.py`
- Stabilitaet: `timeout=30` und `PRAGMA busy_timeout=30000`
- Schema-Erstellung:
  - `ItemRepository.ensure_schema()` fuer fachliche Tabellen
  - `ConfigRepository.ensure_schema()` fuer Setup/Secrets

## Endpoint-Kompatibilitaet

Die Route-Registrierung nutzt Endpoint-Namen aus dem Altbestand (`index`, `item`, `add`, `update_item`, `set_alert`, ...), damit bestehende Templates ohne Bruch weiterlaufen.

## Fehlerstrategie

- Externe Calls (Steam/Telegram) sind defensiv und liefern `None`/`False` statt harter Abbrueche.
- Nutzerfluss bleibt stabil: Netzwerkfehler blockieren die UI nicht komplett.

## Naechste Refactor-Schritte

1. `AlertService` separat extrahieren.
2. `PriceService` separat extrahieren.
3. Repository-Tests mit temporaerer SQLite-DB.
4. API-/HTML-Endpunkte schrittweise in Blueprints aufteilen.
