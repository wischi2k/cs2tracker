// static/js/chart-helpers.js
(function () {
  let _chart = null;

  function eurTick(v) {
    // Chart.js ruft Ticks teils mit String auf → defensiv formatieren
    const n = Number(v);
    if (!Number.isFinite(n)) return v;
    return n.toFixed(2) + " €";
  }

  // Exporte die Funktion global
  window.renderDetailChart = function renderDetailChart(canvasId, d) {
    const el = document.getElementById(canvasId);
    if (!el) return; // kein Canvas im DOM

    // Falls bereits ein Chart existiert (Seitenwechsel / Neuaufbau), zerstören
    if (_chart) {
      try { _chart.destroy(); } catch (_) {}
      _chart = null;
    }

    // Daten sicher aufbereiten
    const ts = Array.isArray(d?.ts) ? d.ts : [];
    const lowest = Array.isArray(d?.lowest) ? d.lowest : [];
    const points = ts.map((t, i) => ({ x: t * 1000, y: lowest[i] }))
                     .filter(p => Number.isFinite(p.y));

    // Wenn keine Daten: Canvas ausblenden und fertig
    if (!points.length) {
      el.replaceWith((() => {
        const div = document.createElement("div");
        div.className = "text-sm text-slate-400";
        div.textContent = "Noch keine Preis-Daten vorhanden.";
        return div;
      })());
      return;
    }

    // Kaufpreis-Linie (optional)
    const buy = typeof d?.buy === "number" ? d.buy : null;
    const buyLine = buy == null ? [] : [
      { x: points[0].x, y: buy },
      { x: points[points.length - 1].x, y: buy }
    ];

    const ctx = el.getContext("2d");

    _chart = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label: "Steam-Preis (€)",
            data: points,
            borderWidth: 2,
            tension: 0.25,
            pointRadius: 0
          },
          ...(buy == null ? [] : [{
            label: "Kaufpreis",
            data: buyLine,
            borderWidth: 1,
            borderDash: [6, 6],
            pointRadius: 0
          }])
        ]
      },
      options: {
        parsing: false,
        animation: false,
        responsive: true,
        maintainAspectRatio: false, // wichtig: wir steuern die Höhe über CSS
        scales: {
          x: {
            type: "time",
            time: { unit: "day" },
            grid: { display: false }
          },
          y: {
            ticks: { callback: eurTick },
            grid: { color: "#33415540" }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  };
})();
