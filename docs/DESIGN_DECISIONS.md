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
- Neue Themes lassen sich durch einen einzigen neuen CSS-Block hinzufügen, ohne bestehende Komponenten anzufassen.
- Tailwind-Klassen, die nicht auf Custom Properties zugreifen können, werden per `!important`-Overrides
  im Abschnitt "Tailwind-Überschreibungen" in `theme.css` gezähmt.

**Gespeicherter Wert:** Der aktive Theme-Key (`dark`, `midnight-jungle`, etc.) liegt in der App-Datenbank
(Settings-Tabelle) und wird serverseitig als `{{ ui_theme }}` in `base.html` eingesetzt:

```html
<html lang="de" data-theme="{{ ui_theme }}">
```

---

## 2. Die vier Themes

### 2.1 Standard Dark (`dark`)

Neutrales, zeitloses Dunkeldesign. Kein starker Farbstich — maximale Lesbarkeit als Default.

| Variable           | Wert        | Rolle                        |
|--------------------|-------------|------------------------------|
| `--c-bg`           | `#0b0f17`   | Fast schwarz, minimaler Blau-Stich |
| `--c-surface`      | `#121821`   | Karten-Hintergrund           |
| `--c-surface-2`    | `#1a2232`   | Hover-States, Inputs         |
| `--c-accent`       | `#39FF14`   | Neon-Grün — primärer Akzent  |
| `--c-btn-action`   | `#d97706`   | Amber für CTA-Buttons        |
| `--c-text-muted`   | `#94a3b8`   | Slate-400 — Metadaten        |

**UX-Entscheidung:** Amber (`#d97706`) als Action-Button-Farbe schafft bewussten Kontrast
zum Neon-Grün des Akzents und signalisiert "Achtung / Aktion".

---

### 2.2 Midnight Jungle Glow (`midnight-jungle`)

Mystisch, dunkel-grün, botanisch. Tiefe Grün-Sättigung als Alternative zum neutralen Dark.

| Variable           | Wert        | Rolle                        |
|--------------------|-------------|------------------------------|
| `--c-bg`           | `#0E1B14`   | Sehr dunkles Waldgrün        |
| `--c-surface`      | `#0B3D2E`   | Tiefes Smaragdgrün           |
| `--c-surface-2`    | `#0d3326`   | Etwas dunkler als Surface    |
| `--c-accent`       | `#39FF14`   | Neon-Grün (identisch zu dark)|
| `--c-text-muted`   | `#1E6F5C`   | Gedämpftes Grün statt Grau   |
| `--c-btn-action`   | `#1E6F5C`   | Grüner CTA (kein Amber)      |

**UX-Entscheidung:** `--c-text-muted` ist hier kein Grau, sondern ein Dunkelgrün —
die Neutraltöne bleiben im Farbcharakter des Themes. Das macht die UI homogener.

---

### 2.3 Arcade Glow Nights (`arcade-glow`)

Retro-Futuristisch, Neon-Lit. Lila-Tiefen, Cyan-Ränder, Hot-Pink CTA.

| Variable           | Wert          | Rolle                          |
|--------------------|---------------|--------------------------------|
| `--c-bg`           | `#0A0A0A`     | Fast reines Schwarz            |
| `--c-surface`      | `#1A0B2E`     | Dunkles Violett                |
| `--c-surface-2`    | `#150924`     | Noch tieferes Violett          |
| `--c-accent`       | `#39FF14`     | Neon-Grün                      |
| `--c-text-muted`   | `#00E5FF`     | Cyan statt Grau                |
| `--c-btn-action`   | `#FF2D55`     | Hot-Pink CTA                   |
| `--c-border`       | `rgba(0,229,255,.12)` | Cyan-Rahmen statt weiß |

**UX-Entscheidung:** Der Hot-Pink CTA (`#FF2D55`) ist der stärkste Akzent-Kontrast aller Themes —
bewusst, weil das gesamte Theme visuell am lautesten ist.

---

### 2.4 Lime Punch Charcoal (`lime-punch`)

Urban, high-contrast, elektrisch. Anthrazit-Basis mit Gold als Button-Akzent.

| Variable           | Wert        | Rolle                          |
|--------------------|-------------|--------------------------------|
| `--c-bg`           | `#0B0F14`   | Dunkles Anthrazit              |
| `--c-surface`      | `#2A2F36`   | Mittleres Anthrazit (hellster Surface-Wert aller Themes) |
| `--c-surface-2`    | `#232830`   | Etwas dunkler                  |
| `--c-accent`       | `#39FF14`   | Neon-Grün                      |
| `--c-btn-action`   | `#FFB000`   | Gold/Amber CTA                 |

**UX-Entscheidung:** `--c-surface` ist mit `#2A2F36` das hellste unter allen vier Themes —
die Karten heben sich dadurch stärker vom Hintergrund ab, was bei Anthrazit funktioniert
(kein Farbstich der die Kontraste verwässert).

---

## 3. Gemeinsame Design-Konstanten

### Akzentfarbe: Neon-Grün `#39FF14` in allen Themes

**Entscheidung:** Der Akzent ist in allen vier Themes identisch.

**Begründung:**
- Schafft eine visuelle Klammer der gesamten App.
- CS2 / Gaming-Kontext: Neon-Grün ist kulturell verankert (HUD-Farben, Night-Vision-Ästhetik).
- Gewinn-Indikatoren (`glow-positive`) verwenden `#4ade80` (ein anderes Grün) — kein Konflikt
  da die Sättigungen sich unterscheiden.

### Gewinn / Verlust — Semantische Farben (theme-unabhängig)

| Klasse           | Farbe     | Bedeutung         |
|------------------|-----------|-------------------|
| `.glow-positive` | `#4ade80` | Gewinn / positiv  |
| `.glow-negative` | `#f87171` | Verlust / negativ |

**Entscheidung:** Diese Farben sind **nicht** theme-variabel — sie sind semantisch
(Rot = Verlust, Grün = Gewinn) und müssen theme-übergreifend konsistent bleiben.

---

## 4. Glow-Effekte

Alle Glow-Effekte basieren auf gestapelten `box-shadow`-Layern (freefrontend / Stripe-Technik).
Mehrere Layer mit abnehmender Intensität erzeugen einen realistischen Lichtabfall.

### Glow-Stufen

```css
--glow-xs: 0 0 5px 1px  rgba(var(--c-accent-rgb),.18);
--glow-sm: 0 0 8px 2px  rgba(var(--c-accent-rgb),.22),
           0 0 18px 4px rgba(var(--c-accent-rgb),.09);
--glow-md: 0 0 10px 2px rgba(var(--c-accent-rgb),.28),
           0 0 22px 6px rgba(var(--c-accent-rgb),.14),
           0 0 40px 10px rgba(var(--c-accent-rgb),.05);
```

| Stufe    | Einsatz                                          |
|----------|--------------------------------------------------|
| `glow-xs`| Buttons hover, Input-Fokus                       |
| `glow-sm`| Karten-Hover, aktive Sidebar-Elemente, Swatches  |
| `glow-md`| `.glow-accent` — stark hervorgehobene Elemente   |

### Spotlight-Effekt (Karten, `glow-card-inner`)

**Technik:** Ein `::before`-Pseudo-Element mit `radial-gradient` folgt dem Mauszeiger.
JS schreibt `--mouse-x` / `--mouse-y` via `mousemove`-Event auf jede Karte.
Startwert `-9999px` hält den Gradient unsichtbar solange die Maus draußen ist.

```css
background: radial-gradient(
  480px circle at var(--mouse-x, -9999px) var(--mouse-y, -9999px),
  rgba(var(--c-accent-rgb), .09),
  transparent 70%
);
```

**Opazität 9%:** Bewusst niedrig gehalten — der Effekt soll subtil unterstützen,
nicht den Karteninhalt überstrahlen.

---

## 5. Ausgewählte Karte (`card-selected`)

**Technik:** Drei kombinierte Effekte.

1. **Pulsierender `box-shadow`** (`selected-card-glow @keyframes`) — Glow am Rand, außerhalb der Karte.
2. **Rotierender Conic-Gradient-Ring** (`card-border-spin @keyframes` + `::after`) — dreht sich
   alle 3 Sekunden um die Karte.
3. **`@property --card-border-angle`** — ermöglicht die CSS-Animation des conic-gradient.

**Wichtige Implementierungs-Entscheidung:**
`.card-selected` setzt `overflow: visible !important` — das ist notwendig, damit der `::after`-Ring
**außerhalb** der Karte rendert. `.glow-card-inner` hat `overflow: hidden` (für den Spotlight-Clip).
Ohne diesen Override würde der Conic-Gradient nach innen geclippt und den Karteninhalt überfluten
(Neon-grüner Hintergrund → Text unleserlich).

Als Ausgleich wird `::before` (Spotlight) via `clip-path: inset(0 round 12px)` auf die Kartenfläche
begrenzt, da `overflow: hidden` für dieses Element nicht mehr greift.

---

## 6. Neon Toggle Switch

Ersetzt klassische Aktivieren/Deaktivieren-Buttons auf der Edit-Seite.
Skeuomorphisch gestaltet: Track + Thumb mit physischem Glüh-Feedback.

**Entscheidung:** Kein JavaScript für den visuellen State — der Toggle-State wird
als CSS-Klasse (`.neon-toggle--on` / `.neon-toggle--off`) serverseitig gerendert.
Ein-/Ausschalten erfolgt weiterhin per Form-POST.

**Begründung:** Konsistent mit dem "progressive enhancement"-Ansatz der App —
JS fällt aus, Form-POSTs funktionieren trotzdem.

---

## 7. Tailwind-Override-Strategie

Tailwind-Klassen die direkt in Templates stehen (z.B. `bg-slate-800`) werden in `theme.css`
per `!important`-Regel auf Theme-Variablen umgebogen:

```css
html[data-theme] .bg-slate-800         { background-color: var(--c-surface-2) !important; }
html[data-theme] .hover\:bg-slate-800:hover { background-color: var(--c-surface-2) !important; }
html[data-theme] .bg-slate-800\/60      { background-color: rgba(var(--c-surface-2-rgb), .60) !important; }
```

**Bekannte Fallstricke:**
- Tailwind mit Opacity-Modifier (`/60`) erzeugt einen **eigenen Klassenamen** (`.bg-slate-800\/60`),
  der separat überschrieben werden muss.
- Tailwind hover-Varianten (`hover:bg-slate-800`) erzeugen ebenfalls einen eigenen Klassenamen
  (`.hover\:bg-slate-800`) — auch dieser braucht eine eigene Override-Regel.
- Deshalb existiert `--c-surface-2-rgb` als RGB-Tripel-Variable (neben `--c-surface-2` als Hex),
  um `rgba(...)` Compositing zu ermöglichen.

---

## 8. Theme-Swatch UX (Settings-Seite)

**Problem:** Die `selected`-CSS-Klasse auf dem Swatch-Label wird serverseitig gesetzt —
nach einem Klick auf einen anderen Swatch passiert visuell nichts bis die Form gespeichert
und die Seite neu geladen wurde.

**Lösung:** Kleines Inline-JS in `settings.html` toggelt die `selected`-Klasse sofort
beim `change`-Event des Radio-Buttons — keine Seiten-Reload nötig für das visuelle Feedback.

---

## 9. Bekannte Design-Kompromisse

| Thema | Kompromiss | Begründung |
|-------|------------|------------|
| Tailwind CDN | Alle Utility-Klassen werden client-seitig generiert, kein Build-Step | Vereinfacht das Deployment auf dem NUC erheblich |
| `!important` Overrides | Viele Theme-Overrides brauchen `!important` | Unvermeidlich wenn Tailwind-Klassen direkt in Templates stehen |
| Keine Dark/Light-Toggle | Nur Dark-Themes | CS2-Kontext; helle Themes wurden nicht benötigt |
| Semantische Farben hardcoded | `glow-positive`/`glow-negative` nicht theme-variabel | Semantik muss theme-übergreifend stabil bleiben |
