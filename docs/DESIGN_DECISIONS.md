# CS2 Tracker — Design & UX Entscheidungen

Dieses Dokument hält alle bewussten Design-Entscheidungen und ihre Begründungen fest,
damit spätere Änderungen nachvollziehbar bleiben.

---

## 1. Theme-System

### Architektur: CSS Custom Properties + `data-theme`

**Entscheidung:** Alle Farben werden als CSS-Variablen auf `html[data-theme="..."]` definiert.
Komponenten greifen ausschließlich auf diese Variablen zu, nie auf Hardcoded-Werte.

**Begründung:**
- Ein Theme-Wechsel erfordert kein JavaScript — nur das `data-theme`-Attribut auf `<html>` ändern.
- Neue Themes lassen sich durch einen einzigen neuen CSS-Block hinzufügen.
- Tailwind-Klassen werden per `!important`-Overrides im Abschnitt „Tailwind-Überschreibungen"
  in `theme.css` auf Custom Properties umgebogen.

**Gespeicherter Wert:** Der aktive Theme-Key liegt in der App-Datenbank (Settings-Tabelle)
und wird serverseitig als `{{ ui_theme }}` in `base.html` eingesetzt:

```html
<html lang="de" data-theme="{{ ui_theme }}">
```

---

### Variablen-Architektur v2: Accent, Glow und Focus sind getrennt

**Problem v1:** Die Akzentfarbe (`--c-accent`) übernahm zu viele Rollen gleichzeitig —
Brand-Farbe, Fokusring, Glow, Hover, Selection. Das führte dazu, dass alle Themes trotz
unterschiedlicher Flächen dieselbe Interaktionssprache hatten. Jede Aktion sah nach
Neon-Grün aus, was auf Dauer ermüdend wirkt.

**Lösung v2:**

| Variable | Rolle | Beispiel |
|----------|-------|---------|
| `--c-accent` / `--c-accent-rgb` | Aktive Zustände, Navigation, kleine Marker | Selected-Bar, Toggle ON, Sidebar Active |
| `--c-accent-2` / `--c-accent-2-rgb` | CTA-Buttons, sekundäre Aktionen | „Jetzt aktualisieren", „Speichern" |
| `--c-focus` / `--c-focus-rgb` | Fokus-Ring bei Keyboard-Navigation | Input Focus, Tab-Ring |
| `--c-glow-rgb` | Schatten, Halos, Spotlight-Gradient | `--glow-xs/sm/md`, Card-Hover, Spotlight |

**Ergebnis:** Themes können jetzt ihren eigenen Leucht-Ton haben. Im Standard-Dark-Theme
ist der Glow z.B. kühles Steel-Cyan statt Neon-Grün — ruhiger, erwachsener, trotzdem lebendig.

---

## 2. Die vier Themes

### 2.1 Standard Dark (`dark`)

**Charakter:** Neutral, ruhig, täglich nutzbar. Kein Gaming-Look.

| Variable | Wert | Bedeutung |
|----------|------|-----------|
| `--c-bg` | `#0b0f17` | Fast schwarz, minimaler Blau-Stich |
| `--c-surface` | `#121821` | Karten-Hintergrund |
| `--c-surface-2` | `#1a2232` | Inputs, Hover-States |
| `--c-accent` | `#39FF14` | Lime — bleibt als Brand-Signal |
| `--c-accent-2` | `#d97706` | Amber — CTA |
| `--c-glow-rgb` | `125,211,252` | **Steel-Cyan** — kein Neon-Grün als Glow mehr |
| `--c-focus-rgb` | `125,211,252` | Steel-Cyan Fokus-Ring |

**Wichtigste Änderung zu v1:** Glow-Effekte verwenden jetzt Steel-Cyan statt Neon-Grün.
Das reduziert den „RGB-Gaming-Hardware-Look" erheblich, ohne die Brand-Farbe zu ändern.

---

### 2.2 Highlighter Noir (`highlighter-noir`)

**Charakter:** Sleek, modern, hochwertig. Premium-SaaS-UI-Charakter. Lime nur als scharfer Marker.

| Variable | Wert | Bedeutung |
|----------|------|-----------|
| `--c-bg` | `#101215` | Fast schwarz, neutraler als dark |
| `--c-surface` | `#171a1f` | Sehr dunkles Grau |
| `--c-surface-2` | `#1f2328` | Dezent heller |
| `--c-accent` | `#39FF14` | Lime — **nur** für aktive States |
| `--c-accent-2` | `#2dd4bf` | Teal — CTA |
| `--c-glow-rgb` | `45,212,191` | **Teal** — Halo folgt dem CTA-Ton |
| `--c-focus-rgb` | `148,163,184` | Slate — sehr dezenter Fokus-Ring |

**Design-Entscheidung:** Lime wird bewusst sparsam eingesetzt — kein flächiger oder
inflationärer Einsatz. Ränder, Divider und Hover-States bleiben kühles Grau.
Kein Retro-Charakter, mehr Produkt-UI.

---

### 2.3 Safety Lime (`safety-lime`)

**Charakter:** Hell, bold, utilitarian. Erinnert an Wayfinding, Event-Signage, Baustellen-Ästhetik.
Konsequenter Widerspruch zum Dark-Mode.

| Variable | Wert | Bedeutung |
|----------|------|-----------|
| `--c-bg` | `#ffffff` | Reines Weiß |
| `--c-surface` | `#f3f4f5` | Helles Concrete-Grau |
| `--c-surface-2` | `#e7eaed` | Etwas dunkler |
| `--c-text` | `#1f2328` | Fast schwarz |
| `--c-accent` | `#2d9900` | **Sattes Lime-Grün** (dunkler als `#39FF14` — lesbar auf weiß) |
| `--c-accent-2` | `#e6b800` | **Construction-Yellow** — CTA |
| `--c-glow-rgb` | `101,163,13` | Soft-Lime für Halos |

**Wichtige Einschränkung:** Lime und Gelb dürfen nicht gleichzeitig überall eingesetzt werden.
Beides sind sehr laute Farben — dosierter Einsatz verhindert, dass die UI wie eine
Warnfarbenfläche wirkt.

**Warum `#2d9900` statt `#39FF14`?** Neon-Lime (`#39FF14`) ist auf weißem Hintergrund
fast unsichtbar — zu wenig Kontrast. `#2d9900` ist ein sattes, warmes Grün mit ausreichend
Kontrast auf weißen und hellgrauen Flächen.

---

### 2.4 Cleanroom Lime (`cleanroom-lime`)

**Charakter:** Präzise, minimal, datenzentriert. Maximal lange nutzbar, keine visuellen Ablenkungen.
Besonders geeignet für Tabellen, Charts und Watchlists.

| Variable | Wert | Bedeutung |
|----------|------|-----------|
| `--c-bg` | `#f8fafc` | Sehr helles Blau-Grau |
| `--c-surface` | `#ffffff` | Reine weiße Karten |
| `--c-surface-2` | `#eef2f6` | Helles Slate |
| `--c-text` | `#0f172a` | Sehr dunkles Slate-Navy |
| `--c-accent` | `#2d9900` | Lime — reiner Signalton |
| `--c-accent-2` | `#2563eb` | **Blau** — ruhige CTA-Farbe |
| `--c-glow-rgb` | `101,163,13` | Sehr sanfter Lime-Halo |

**Design-Entscheidung:** Blau als CTA (`#2563eb`) ist bewusst gewählt — es schafft maximalen
Kontrast zur Lime-Signalfarbe. Nicht jede Aktion muss Lime sein. Blau als „professionelle
Aktionsfarbe" passt zum klinisch-präzisen Charakter des Themes.

---

## 3. Gemeinsame Design-Konstanten

### Semantische Farben — theme-unabhängig hardcoded

| Klasse | Farbe | Bedeutung |
|--------|-------|-----------|
| `.glow-positive` | `#4ade80` | Gewinn / positiver Delta |
| `.glow-negative` | `#f87171` | Verlust / negativer Delta |

**Begründung:** Rot = Verlust, Grün = Gewinn ist eine universelle semantische Konvention.
Diese Farben dürfen nicht theme-variabel sein — sie müssen in allen vier Themes gleich lesbar und
gleich bedeutsam sein.

---

## 4. Glow-Effekte

### Grundprinzip: Tiefe statt Leuchten

**v1-Problem:** Mehrfach gestapelte Neon-Glows führten zu visueller Ermüdung bei längerer Nutzung
und zu einem generellen „Gaming-Hardware"-Look.

**v2-Lösung:** Glow-Effekte sind reduziert und subtiler:
- Kein mehrfach gestapelter Neon-Glow mehr
- Stattdessen: 1px Halo-Ring (`0 0 0 1px rgba(...)`) + weicher Drop-Shadow
- `--c-glow-rgb` ist theme-abhängig → jedes Theme hat seinen eigenen Leucht-Ton

```css
--glow-xs: 0 0 0 1px rgba(var(--c-glow-rgb), .18);
--glow-sm: 0 0 0 1px rgba(var(--c-glow-rgb), .20), 0 6px 20px rgba(0,0,0,.12);
--glow-md: 0 0 0 1px rgba(var(--c-glow-rgb), .24), 0 10px 30px rgba(0,0,0,.16), ...;
```

### Spotlight-Effekt (Karten, `glow-card-inner`)

Bleibt bestehen, aber mit reduzierter Opazität (6% statt 9%) und nutzt `--c-glow-rgb`
statt `--c-accent-rgb`. Der Effekt folgt dem Mauszeiger via `--mouse-x`/`--mouse-y` (JS).

---

## 5. Ausgewählte Karte (`card-selected`)

### Design-Änderung v1 → v2

**v1 (verworfen):** Rotierender Conic-Gradient-Ring (`@property --card-border-angle` +
`card-border-spin @keyframes`) + pulsierender Box-Shadow. Probleme:
- `overflow: hidden` auf dem Karten-Element clippte den `::after`-Ring nach **innen**
  statt nach außen → Karte leuchtete komplett neon-grün, Text war kaum lesbar.
- Technisch komplex, visuell zu dominant.

**v2 (aktuell):** Drei ruhigere Elemente:
1. **Accent-Border:** `border-color: rgba(var(--c-accent-rgb), .40)` — subtile Rahmenlinie
2. **Gradient-Tint:** Minimale Lime-Aufhellung der Kartenfläche (5% → 1,5% von oben nach unten)
3. **Left-Bar:** 3px breiter vertikaler Balken am linken Rand in `var(--c-accent)`

**Begründung:** Der Left-Bar-Marker ist theme-unabhängig wiedererkennbar, barrierereduziertert
(nicht nur Farbe als Signal) und vermeidet die visuelle Dominanz eines Glow-Effekts.

---

## 6. Fokus-System

**v1:** Input-Fokus nutzte `--c-accent` (Lime) für Border und `--glow-xs` (Lime-Glow).

**v2:** Separater `--c-focus-rgb`-Token:
```css
--focus-ring: 0 0 0 2px rgba(var(--c-focus-rgb), .30);
```
Inputs nutzen `--c-focus-rgb` für Border und `--focus-ring` für den Schatten.
Im Standard-Dark-Theme ist das Steel-Cyan — deutlich dezenter als Neon-Lime-Fokus.

---

## 7. Tailwind-Override-Strategie

Tailwind CDN generiert Klassen dynamisch. Wichtige Fallstricke:

**Opacity-Modifier** (`bg-slate-800/60`) erzeugen eigene CSS-Klassenamen:
```css
html[data-theme] .bg-slate-800\/60 { background: rgba(var(--c-surface-2-rgb), .60) !important; }
```

**Hover-Varianten** (`hover:bg-slate-800`) erzeugen ebenfalls eigene Klassenamen:
```css
html[data-theme] .hover\:bg-slate-800:hover { background: var(--c-surface-2) !important; }
```

**Light-Theme-Kompatibilität:** Alle Text-Overrides (`text-slate-300/400`) und
Hintergrund-Overrides (`bg-slate-900/800/700`) nutzen CSS-Variablen, die in Light-Themes
auf helle Werte gesetzt sind. Dadurch funktionieren dieselben Override-Regeln in allen Themes.

**Vollständig überschriebene Klassen:** `bg-slate-900/800/700/600/500/400` inklusive
Opacity-Varianten, `hover:bg-slate-*`, `text-slate-100/200/300/400/500`, `text-gray-300/400`,
`border-slate-700/600`.

**Zusatzvariable `--c-interactive`/`--c-interactive-hi`:** Für `bg-slate-700`/`bg-slate-600`
(interaktive Elemente wie Edit-Buttons, Iconplatzhalter). In Dark-Themes dunkles Blau-Grau,
in Light-Themes mittleres Concrete-Grau.

---

## 8. Theme-Swatch UX (Settings-Seite)

Die Swatch-Dots zeigen nicht nur `--c-bg` und `--c-surface`, sondern ab v2 den
**Glow-/CTA-Ton** des Themes als dritten Dot. Das gibt auf der Settings-Seite eine
ehrlichere Vorschau des visuellen Charakters, bevor das Theme gespeichert wird.

Sofortiges visuelles Feedback beim Klick: Kleines Inline-JS in `settings.html`
toggelt die `selected`-Klasse direkt beim Radio-`change`-Event.

---

## 9. Chart-Tokens

Charts und Datenvisualisierungen nutzen eigene Token statt UI-Akzentfarben:

```css
--chart-1: var(--c-accent);   /* erste Datenserie */
--chart-2: #60a5fa;           /* zweite Datenserie — Blau */
--chart-3: #f59e0b;           /* dritte Datenserie — Amber */
--chart-4: #f472b6;           /* vierte Datenserie — Pink */
--chart-grid: rgba(148,163,184,.15);
```

Diese Token sind in `:root` definiert und theme-unabhängig (außer `--chart-1`),
damit Datenpunkte in verschiedenen Themes immer dieselbe Bedeutung haben.

---

## 10. Bekannte Design-Kompromisse

| Thema | Kompromiss | Begründung |
|-------|------------|------------|
| Tailwind CDN | Alle Klassen client-seitig generiert, kein Build-Step | Vereinfacht Deployment auf NUC erheblich |
| `!important` Overrides | Viele Theme-Overrides brauchen `!important` | Unvermeidlich wenn Tailwind-Klassen direkt in Templates stehen |
| Neon-Lime für Light-Themes | `#39FF14` wäre auf weißem BG kaum sichtbar → `#2d9900` | Kontrastverhältnis auf weiß/hellgrau benötigt satteres Grün |
| Semantische Farben hardcoded | `glow-positive/negative` nicht theme-variabel | Semantik muss theme-übergreifend stabil bleiben |
| Neon-Toggle nutzt noch `--c-accent` direkt | Toggle-Zustand als Status-Indikator bleibt Lime | Deliberate: Toggle zeigt AN/AUS — Lime als globales „an"-Signal ist konsistent |
