# CS2 Tracker — Theme-Überarbeitung

## Ziel

Das bestehende Theme-System soll so überarbeitet werden, dass sich die Themes im Gesamteindruck deutlich stärker voneinander unterscheiden, ohne an Nutzbarkeit zu verlieren.

Das aktuelle Problem ist nicht die technische Umsetzung des Theme-Systems, sondern die visuelle Nähe der Themes untereinander. Der Hauptgrund dafür ist, dass dieselbe Neon-Lime-Akzentlogik in allen Themes als gemeinsame visuelle Klammer genutzt wird. Dadurch wirken unterschiedliche Themes trotz anderer Flächen- und Hintergrundfarben im Ergebnis zu ähnlich. Genau diese Entscheidung ist auch in den bisherigen Design-Entscheidungen dokumentiert: identischer Akzent in allen Themes, dazu Glow-Effekte auf Basis von `--c-accent`. :contentReference[oaicite:0]{index=0}

## Bestehendes Problem

Aktuell übernimmt die Akzentfarbe in mehreren Themes gleichzeitig zu viele Rollen:

- Brand-/Highlight-Farbe
- Fokusfarbe
- Hoverfarbe
- Glowfarbe
- teilweise Selection-Farbe

Dadurch entsteht kein klarer visueller Unterschied zwischen den Themes. Es ändern sich zwar Hintergrund- und Surface-Töne, aber die Interaktionssprache fühlt sich weitgehend gleich an.

Zusätzlich sorgt der konsequente Einsatz von Neon-Grün in Kombination mit Glow-Effekten dafür, dass die UI schnell sehr ähnlich, teilweise anstrengend und in Summe weniger hochwertig wirkt, als sie eigentlich sein könnte.

## Grundsätzliche Designentscheidung für die Überarbeitung

Die Themes sollen künftig nicht nur farblich, sondern auch funktional und atmosphärisch klar getrennt werden.

### Geplante Rollen der Themes

#### 1. `dark`
Der bestehende Standard-Dark-Mode bleibt grundsätzlich unangetastet.

Er soll weiterhin das neutrale, zeitlose und am breitesten einsetzbare Standard-Theme bleiben. Lediglich die bisher sehr präsenten neon-grünen Glow-, Fokus- und Halo-Effekte sollen durch deutlich dezentere, passendere Effekte ersetzt werden.

Ziel:
- ruhig
- erwachsen
- gut lesbar
- täglich angenehm nutzbar

#### 2. `highlighter-noir`
Dieses Theme soll das elegante, moderne Dark-Theme werden.

Statt eines verspielten Neon-Looks soll es eher wie ein hochwertiges SaaS-/Produktivitäts-Interface wirken: dunkle Layer, klare Hierarchie, Lime nur als scharfer Marker für aktive Zustände.

Ziel:
- sleek
- modern
- hochwertig
- produktiv

#### 3. `safety-lime`
Dieses Theme soll das helle Gegenstück zum Standard-Dark-Mode sein.

Es soll bewusst dem Dark-Mode widersprechen: helle Basis, concrete-/utility-artige Flächen, signalhafte Akzente in Lime und Construction Yellow. Der Charakter soll an Wayfinding, Event-Signage und funktionale Leitsysteme erinnern, dabei aber trotzdem angenehm benutzbar bleiben.

Ziel:
- bold
- utilitarian
- street-smart
- klar in der Benutzerführung

#### 4. `cleanroom-lime`
Dieses Theme soll das ruhigste und datenfreundlichste helle Theme werden.

Es soll präzise, klinisch, minimal und sehr gut für Tabellen, Charts, Preisverläufe und detailreiche Datendarstellung geeignet sein. Lime bleibt hier Signalton, darf aber nur sehr gezielt eingesetzt werden.

Ziel:
- präzise
- minimal
- datenzentriert
- lange angenehm nutzbar

---

## Wichtigste technische Designanpassung

### Accent und Glow voneinander trennen

Aktuell basiert die visuelle Identität vieler Komponenten zu stark auf einer einzigen Akzentlogik. Künftig sollen Akzentfarbe, CTA-Farbe, Fokusfarbe und Glowfarbe getrennt werden.

Empfohlene zusätzliche Variablen:

```css
--c-accent: ...;       /* Links, aktive Zustände, kleine Highlights */
--c-accent-2: ...;     /* CTA / sekundärer Akzent */
--c-focus: ...;        /* Fokus-Ring */
--c-glow-rgb: ...;     /* Schatten / Halo / Glow */
Ziel dieser Trennung
Themes unterscheiden sich stärker
Interaktionszustände fühlen sich hochwertiger an
nicht jede Hervorhebung sieht automatisch nach Neon-Effekt aus
bessere visuelle Hierarchie
weniger visuelle Ermüdung bei längerer Nutzung
Konkrete Anforderungen pro Theme
1) dark — nur Neon-Effekte entschärfen
Grundsatz

Dieses Theme soll strukturell und farblich im Kern bestehen bleiben.

Was geändert werden soll
Neon-grüne Glow-Effekte ersetzen
Fokus- und Halo-Effekte dezenter machen
Akzentgrün nicht komplett entfernen, sondern stärker auf kleine Signale begrenzen
CTA-Farbe in Amber kann bestehen bleiben
Gewünschte Wirkung
weniger „RGB-/Gaming-Hardware-Look“
mehr hochwertiges, neutrales Dashboard
besser für tägliche Nutzung
Empfehlung
--c-accent darf Lime bleiben
Glow/Fokus eher in Richtung kühles Steel/Cyan statt Neon-Grün
2) highlighter-noir — elegantes Dark-Theme
Grundsatz

Dieses Theme soll das modernste und edelste Dark-Theme sein.

Was wichtig ist
Lime nur für aktive Zustände, Toggles, Selections und Status
keine flächige oder inflationäre Nutzung von Lime
Ränder, Divider, Text-Hierarchien und Hover-Zustände ruhiger halten
weniger Retro-/Arcade-Charakter, mehr Produkt-UI
Gewünschte Wirkung
moderne Dark-Layer
klare Struktur
subtiler Premium-Charakter
3) safety-lime — helles Wayfinding-/Utility-Theme
Grundsatz

Dieses Theme soll bewusst hell und plakativ sein, ohne billig oder anstrengend zu wirken.

Was wichtig ist
Weiß als Hauptfläche
Concrete-/Gray-Töne für Flächen, Karten, Inputs und Struktur
Lime für aktive Navigation, primäre Marker und ausgewählte Fokuspunkte
Gelb für CTA, Warnung oder besondere Lenkung
Lime und Gelb nicht gleichzeitig überall einsetzen
Gewünschte Wirkung
klare Führung
urbaner Utility-Look
hohe Auffindbarkeit wichtiger Aktionen
Wichtige Einschränkung

Das Theme darf nicht wie eine reine Warnfarbenfläche wirken. Lime und Gelb müssen sehr dosiert eingesetzt werden, sonst kippt die UI in Richtung plakativ und unruhig.

4) cleanroom-lime — helles, ruhiges Daten-Theme
Grundsatz

Dieses Theme soll maximale Klarheit und lange Nutzbarkeit priorisieren.

Was wichtig ist
sehr helle, saubere Basis
Slate-/Navy-Töne für Typografie und sekundäre Ebenen
Lime nur als Signalton
optional ein kühler Gegenakzent für CTAs, damit nicht jede Aktion lime sein muss
besonders geeignet für Tabellen, Statistiken, Watchlists und Visualisierungen
Gewünschte Wirkung
präzise
clean
professionell
ruhig trotz klarer Signalpunkte
Empfehlungen für Interaktionsdesign
Glow allgemein reduzieren

Die bisherigen Glow-Effekte wirken teilweise zu präsent. Für die Überarbeitung sollten Glow- und Halo-Effekte grundsätzlich zurückhaltender eingesetzt werden.

Ziel
mehr Tiefe statt mehr Leuchten
mehr hochwertige Layering-Wirkung
weniger visuelle Ermüdung
bessere Nutzbarkeit über längere Sessions
Empfehlung

Statt starker neonartiger Mehrfach-Glows lieber:

subtile 1px-Halo-Ringe
weichere Shadows
klare Fokus-Ringe
leichte Surface-Aufhellung bei Hover oder Auswahl
Selected State nicht nur über Farbe lösen

Der Zustand card-selected sollte nicht ausschließlich über Glow oder Akzentfarbe erkennbar sein.

Zusätzlich sinnvoll:

leicht stärkere Border
minimale Surface-Helligkeitsänderung
optional Top-Bar, Check-Icon oder Marker
klarer Fokus-/Active-State auch ohne dominanten Glow

Ziel:

Theme-unabhängige Wiedererkennbarkeit
bessere Zugänglichkeit
weniger Abhängigkeit von leuchtenden Effekten
Eigene Chart-Farben definieren

Charts und Datenvisualisierungen sollten nicht ausschließlich dieselben UI-Akzentfarben recyceln wie Buttons, Links und Fokuszustände.

Empfehlung:
eigene Design-Tokens für Chart-Serien und Grid-Lines anlegen, damit sich Datendarstellung kontrollierter und differenzierter verhält.

Beispiel:

--chart-1: var(--c-accent);
--chart-2: ...;
--chart-3: ...;
--chart-4: ...;
--chart-grid: ...;

Ziel:

Daten besser differenzierbar
weniger visuelle Überladung
Themes wirken ausgereifter
Gewünschtes Ergebnis

Nach der Überarbeitung sollen die Themes nicht mehr nur wie Varianten derselben Neon-Dark-Idee wirken, sondern wie eigenständige visuelle Modi mit klarem Charakter:

dark = neutraler Standard
highlighter-noir = edles modernes Dark-Theme
safety-lime = helles Utility-/Wayfinding-Theme
cleanroom-lime = helles präzises Daten-Theme

Das Theme-System soll damit weiterhin technisch konsistent bleiben, aber visuell deutlich mehr Spannweite und Wiedererkennbarkeit bekommen.


## CSS-Vorschlag

```css
/* =========================================================
   Theme refactor proposal for CS2 Tracker
   Goal:
   - keep dark structurally intact, but reduce neon-green glow
   - create clearly different theme personalities
   - separate accent, focus and glow behavior
   ========================================================= */

/* ---------------------------------------------------------
   Shared design tokens
   --------------------------------------------------------- */

:root {
  --radius-md: 12px;

  /* softer, more usable interaction shadows */
  --glow-xs:
    0 0 0 1px rgba(var(--c-glow-rgb), .18);

  --glow-sm:
    0 0 0 1px rgba(var(--c-glow-rgb), .22),
    0 8px 24px rgba(0, 0, 0, .14);

  --glow-md:
    0 0 0 1px rgba(var(--c-glow-rgb), .24),
    0 12px 32px rgba(0, 0, 0, .18);

  --focus-ring:
    0 0 0 2px rgba(var(--c-focus-rgb), .28);

  /* optional chart tokens */
  --chart-1: var(--c-accent);
  --chart-2: #60a5fa;
  --chart-3: #f59e0b;
  --chart-4: #f472b6;
  --chart-grid: rgba(148, 163, 184, .18);
}

/* ---------------------------------------------------------
   1) Standard Dark (`dark`)
   Keep base palette. Only replace loud neon glows with
   a more restrained cool focus/glow language.
   --------------------------------------------------------- */

html[data-theme="dark"] {
  --c-bg: #0b0f17;
  --c-surface: #121821;
  --c-surface-2: #1a2232;

  --c-bg-rgb: 11, 15, 23;
  --c-surface-rgb: 18, 24, 33;
  --c-surface-2-rgb: 26, 34, 50;

  --c-text: #f8fafc;
  --c-text-muted: #94a3b8;

  --c-accent: #39FF14;         /* keep lime as brand/active signal */
  --c-accent-rgb: 57, 255, 20;

  --c-accent-2: #d97706;       /* CTA */
  --c-accent-2-rgb: 217, 119, 6;

  --c-focus: #7dd3fc;          /* softer focus language */
  --c-focus-rgb: 125, 211, 252;

  --c-glow-rgb: 125, 211, 252; /* replace neon-green glow with cool steel/cyan */
  --c-border: rgba(148, 163, 184, .14);
}

/* ---------------------------------------------------------
   2) Highlighter Noir Interface (`highlighter-noir`)
   Premium dark UI with lime only as a sharp signal.
   --------------------------------------------------------- */

html[data-theme="highlighter-noir"] {
  --c-bg: #101215;
  --c-surface: #171A1F;
  --c-surface-2: #1F2328;

  --c-bg-rgb: 16, 18, 21;
  --c-surface-rgb: 23, 26, 31;
  --c-surface-2-rgb: 31, 35, 40;

  --c-text: #E9ECEF;
  --c-text-muted: #98A2AD;

  --c-accent: #39FF14;         /* active state / selected / live */
  --c-accent-rgb: 57, 255, 20;

  --c-accent-2: #2dd4bf;       /* CTA / secondary action */
  --c-accent-2-rgb: 45, 212, 191;

  --c-focus: #94a3b8;
  --c-focus-rgb: 148, 163, 184;

  --c-glow-rgb: 57, 255, 20;   /* may stay lime, but used subtly */
  --c-border: rgba(233, 236, 239, .10);
}

/* ---------------------------------------------------------
   3) Safety Lime Concrete (`safety-lime`)
   Light, bold utility theme inspired by signage / wayfinding.
   --------------------------------------------------------- */

html[data-theme="safety-lime"] {
  --c-bg: #FFFFFF;
  --c-surface: #F3F4F4;
  --c-surface-2: #E7EAED;

  --c-bg-rgb: 255, 255, 255;
  --c-surface-rgb: 243, 244, 244;
  --c-surface-2-rgb: 231, 234, 237;

  --c-text: #1F2328;
  --c-text-muted: #5f6b76;

  --c-accent: #39FF14;         /* primary route / active / key marker */
  --c-accent-rgb: 57, 255, 20;

  --c-accent-2: #FFD400;       /* CTA / warning / directional emphasis */
  --c-accent-2-rgb: 255, 212, 0;

  --c-focus: #84cc16;          /* softened lime for focus ring */
  --c-focus-rgb: 132, 204, 22;

  --c-glow-rgb: 132, 204, 22;  /* soft green halo only */
  --c-border: rgba(60, 64, 67, .14);
}

/* ---------------------------------------------------------
   4) Cleanroom Lime White (`cleanroom-lime`)
   Precise, quiet, data-friendly light theme.
   --------------------------------------------------------- */

html[data-theme="cleanroom-lime"] {
  --c-bg: #F8FAFC;
  --c-surface: #FFFFFF;
  --c-surface-2: #EEF2F6;

  --c-bg-rgb: 248, 250, 252;
  --c-surface-rgb: 255, 255, 255;
  --c-surface-2-rgb: 238, 242, 246;

  --c-text: #0F172A;
  --c-text-muted: #475569;

  --c-accent: #39FF14;         /* signal only */
  --c-accent-rgb: 57, 255, 20;

  --c-accent-2: #2563EB;       /* calmer action color for buttons / links */
  --c-accent-2-rgb: 37, 99, 235;

  --c-focus: #84cc16;
  --c-focus-rgb: 132, 204, 22;

  --c-glow-rgb: 132, 204, 22;
  --c-border: rgba(51, 65, 85, .12);
}

/* =========================================================
   Suggested usage patterns
   ========================================================= */

/* Base */
html[data-theme] body {
  background: var(--c-bg);
  color: var(--c-text);
}

/* Cards / panels */
html[data-theme] .ui-surface {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
}

html[data-theme] .ui-surface-alt,
html[data-theme] .bg-slate-800,
html[data-theme] .hover\:bg-slate-800:hover {
  background: var(--c-surface-2) !important;
}

/* Inputs */
html[data-theme] .ui-input,
html[data-theme] input,
html[data-theme] select,
html[data-theme] textarea {
  background: var(--c-surface-2);
  color: var(--c-text);
  border: 1px solid var(--c-border);
}

html[data-theme] .ui-input:focus,
html[data-theme] input:focus,
html[data-theme] select:focus,
html[data-theme] textarea:focus {
  outline: none;
  border-color: rgba(var(--c-focus-rgb), .45);
  box-shadow: var(--focus-ring);
}

/* Primary action
   For better usability, use accent-2 for CTA instead of pure lime */
html[data-theme] .btn-primary,
html[data-theme] .btn-action {
  background: var(--c-accent-2);
  color: #0b0f17;
  border: 1px solid transparent;
}

html[data-theme="dark"] .btn-primary,
html[data-theme="dark"] .btn-action,
html[data-theme="highlighter-noir"] .btn-primary,
html[data-theme="highlighter-noir"] .btn-action {
  color: #ffffff;
}

html[data-theme] .btn-primary:hover,
html[data-theme] .btn-action:hover {
  box-shadow: var(--glow-sm);
  transform: translateY(-1px);
}

/* Accent usage
   Keep lime for active states, not for every interaction */
html[data-theme] .is-active,
html[data-theme] .nav-link.active,
html[data-theme] .tab.active,
html[data-theme] .toggle--on {
  color: var(--c-accent);
  border-color: rgba(var(--c-accent-rgb), .35);
}

/* Links */
html[data-theme] a {
  color: var(--c-accent-2);
}

html[data-theme] a:hover {
  color: var(--c-accent);
}

/* Selected card
   Do not rely on glow alone */
html[data-theme] .card-selected {
  position: relative;
  border: 1px solid rgba(var(--c-accent-rgb), .42);
  box-shadow: var(--glow-sm);
  background:
    linear-gradient(
      180deg,
      rgba(var(--c-accent-rgb), .05),
      rgba(var(--c-accent-rgb), .015)
    ),
    var(--c-surface);
}

/* Optional selected marker */
html[data-theme] .card-selected::after {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  border-radius: 12px 0 0 12px;
  background: var(--c-accent);
}

/* Hover cards
   More depth, less neon */
html[data-theme] .glow-card-inner:hover,
html[data-theme] .ui-surface:hover {
  border-color: rgba(var(--c-glow-rgb), .26);
  box-shadow: var(--glow-sm);
}

/* Optional spotlight effect toned down */
html[data-theme] .glow-card-inner::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background:
    radial-gradient(
      420px circle at var(--mouse-x, -9999px) var(--mouse-y, -9999px),
      rgba(var(--c-glow-rgb), .06),
      transparent 68%
    );
  opacity: 1;
}

/* Muted text */
html[data-theme] .text-muted,
html[data-theme] .ui-meta {
  color: var(--c-text-muted);
}

/* Dividers */
html[data-theme] hr,
html[data-theme] .ui-divider {
  border-color: var(--c-border);
}

/* Data viz helpers */
html[data-theme] .chart-grid line {
  stroke: var(--chart-grid);
}

html[data-theme] .series-1 { stroke: var(--chart-1); fill: var(--chart-1); }
html[data-theme] .series-2 { stroke: var(--chart-2); fill: var(--chart-2); }
html[data-theme] .series-3 { stroke: var(--chart-3); fill: var(--chart-3); }
html[data-theme] .series-4 { stroke: var(--chart-4); fill: var(--chart-4); }

/* Semantic colors remain theme-independent if desired */
.glow-positive { color: #4ade80; }
.glow-negative { color: #f87171; }