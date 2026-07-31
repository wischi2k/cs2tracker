# UI/UX-Bewertung

Stand: 2026-07-31 · Basis: `templates/`, `static/css/theme.css` (816 Zeilen), `static/js/`

## 1. Optische Bewertung — Bewertung: gut, überdurchschnittlich für ein Hobbyprojekt

Stärken:

- **Echtes Design-System statt Ad-hoc-Styling.** `theme.css` definiert eine dokumentierte Variablen-Hierarchie (Flächen-Ebenen `--c-bg` → `--c-panel` → `--c-surface` → `--c-interactive`, Akzent-/Glow-/Fokus-Töne) und vier vollständige Themes. Das ist die Struktur, die man sonst in Produkt-Teams sieht.
- **Konsistente Komponenten-Klassen** (`.btn`, `.input`, `.nav-link`, `.kpi-card`, `.card`) — Themes wirken automatisch auf alle Elemente.
- **Gute Detail-Entscheidungen:** Empty-State mit Illustration und Call-to-Action auf dem Dashboard, KPI-Kacheln im Detail-Panel, farbcodierte Δ-Werte mit Glow, Cache-Busting für Item-Icons, klare Trennung Inventar/Tracking in der Sidebar.
- Die Theme-Beschreibungen („Highlighter Noir", „Cleanroom Lime") zeigen bewusste Design-Absicht — kein Zufalls-Styling.

Schwächen im visuellen Bereich sind klein: Der Neon-Grün-Akzent (`#39FF14`) im Standard-Dark-Theme ist geschmackssache und kollidiert leicht mit dem Amber-CTA; die Glow-Effekte sind auf schwächeren Geräten (mousemove-Listener pro Karte in `glow-effects.js`) potenziell teuer, aber vertretbar.

## 2. UX-Schwächen — hier liegt das eigentliche Verbesserungspotenzial

### 2.1 Nicht responsiv (wichtigster Punkt)

`index.html` nutzt ein fixes `grid-cols-[320px,1fr]`. Auf einem Smartphone — dem realistischsten Gerät für „mal eben Portfolio checken" — bricht das Layout; es gibt keinen einzigen Breakpoint im Projekt. Kommerzielle Tracker sind alle mobile-first.

**Empfehlung:** Unter `md:` die Sidebar zur horizontal scrollbaren Kartenleiste oder zu einer eigenen Listen-Ansicht machen; KPI-Streifen umbrechen lassen (`flex-wrap` ist teils schon da). Aufwand: 1 Abend, größter UX-Gewinn pro Stunde.

### 2.2 Full-Page-Reload bei jeder Interaktion

Jeder Item-Klick, jeder Kategorie-Filter, jeder Refresh lädt die komplette Seite neu (der vorhandene `router.js` ist nicht eingebunden). Das kostet gefühlte Geschwindigkeit und wirft Scroll-Position weg.

**Empfehlung:** Kein SPA-Umbau nötig — [htmx](https://htmx.org) (~14 KB, self-hostbar) passt perfekt zur Server-Rendered-Architektur: Detail-Panel per `hx-get` austauschen, Kategorie-Filter per `hx-trigger="change"` ohne „Anwenden"-Button.

### 2.3 Fehlende Basis-Werkzeuge bei wachsender Item-Liste

- **Keine Suche** — ab ~20 Items wird die Sidebar unübersichtlich.
- **Keine Sortierung** (nach Δ, Wert, Name; aktuell fix alphabetisch aus dem SQL).
- **Kategorie-Filter braucht einen Submit-Klick** statt direkt bei Auswahl zu filtern.

### 2.4 Informationsdichte der Item-Cards

Die Cards zeigen absolute Werte, aber **keine Prozent-Änderung** — die relevanteste Zahl beim schnellen Scannen („+12 %" sagt mehr als „+3,40 €"). Ebenfalls üblich bei allen kommerziellen Tools: **Mini-Sparkline** (7-Tage-Trend) pro Card und 24h/7d/30d-Badges.

### 2.5 Chart

Der Detail-Chart zeigt immer die gesamte Historie. Es fehlen:

- Zeitraum-Schalter (7T / 30T / 90T / 1J / Max)
- Hover-Tooltip mit Datum + Netto-Wert (falls nicht vorhanden)
- Markierung des Kaufzeitpunkts zusätzlich zur Kaufpreis-Linie
- Bei langen Zeiträumen: Aggregation (Tages-Durchschnitt), sonst wird die Linie zackig und langsam

### 2.6 Kleinere Punkte

- „Steam-Fee: 15 %" als statischer Text im Header wirkt wie ein Debug-Overlay — gehört in ein Tooltip/Info-Icon bei den Netto-Werten.
- Löschen eines Items hat keine Bestätigung (ein POST, Historie unwiderruflich weg) — mindestens ein `confirm()`-Dialog, besser Soft-Delete (siehe Feature-Roadmap: Verkaufs-Workflow).
- Flash-Messages verschwinden nicht automatisch und sind nicht schließbar.
- `<title>` ist immer „CS2 Tracker" — Item-Name im Titel wäre für Browser-Historie/Tabs hilfreich.
- Barrierefreiheit: Fokus-Ringe sind vorbildlich definiert (`--c-focus-rgb`), aber Icon-Buttons ohne `aria-label` und die reine Farb-Codierung von Gewinn/Verlust (grün/rot) ohne zweites Signal (▲/▼) sind ausbaufähig.

## 3. Priorisierte UX-Maßnahmen

| # | Maßnahme | Aufwand | Wirkung |
|---|---|---|---|
| 1 | Responsive Layout (Mobile) | 1 Abend | sehr hoch |
| 2 | %-Änderung + Trend-Indikator auf Cards | 2–3 h | hoch |
| 3 | Suchfeld + Sortierung in der Sidebar | 3–4 h | hoch |
| 4 | Chart-Zeitraum-Schalter | 3–4 h | hoch |
| 5 | htmx für Detail-Panel & Filter | 1 Abend | mittel–hoch |
| 6 | Lösch-Bestätigung | 30 min | mittel (Datenschutz vor sich selbst) |
| 7 | Kategorie-Filter ohne Submit-Button | 30 min | klein, aber täglich spürbar |
| 8 | Sparklines auf Cards | 1 Abend | mittel (Politur) |
