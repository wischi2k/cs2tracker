// static/js/chart-helpers.js
(function () {
  let _chart = null;

  function eurTick(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return v;
    return n.toFixed(2) + " EUR";
  }

  window.renderDetailChart = function renderDetailChart(canvasId, d) {
    const el = document.getElementById(canvasId);
    if (!el) return;

    if (_chart) {
      try {
        _chart.destroy();
      } catch (_) {}
      _chart = null;
    }

    const ts = Array.isArray(d?.ts) ? d.ts : [];
    const lowest = Array.isArray(d?.lowest) ? d.lowest : [];
    const points = ts
      .map((t, i) => ({ x: t * 1000, y: lowest[i] }))
      .filter((p) => Number.isFinite(p.y));

    if (!points.length) {
      el.replaceWith((() => {
        const div = document.createElement("div");
        div.className = "text-sm text-slate-400";
        div.textContent = "Noch keine Preis-Daten vorhanden.";
        return div;
      })());
      return;
    }

    const buy = typeof d?.buy === "number" ? d.buy : null;
    const buyLine =
      buy == null
        ? []
        : [
            { x: points[0].x, y: buy },
            { x: points[points.length - 1].x, y: buy },
          ];

    const ctx = el.getContext("2d");

    const triggeredAt = typeof d?.triggered_at === "number" ? d.triggered_at * 1000 : null;
    const triggeredAtPlugin = {
      id: "triggeredAt",
      afterDraw(chart) {
        if (!triggeredAt) return;
        const xAxis = chart.scales.x;
        const yAxis = chart.scales.y;
        const xPos = xAxis.getPixelForValue(triggeredAt);
        if (xPos < xAxis.left || xPos > xAxis.right) return;
        const c = chart.ctx;
        c.save();
        c.beginPath();
        c.moveTo(xPos, yAxis.top);
        c.lineTo(xPos, yAxis.bottom);
        c.strokeStyle = "#f59e0b";
        c.lineWidth = 2;
        c.setLineDash([4, 4]);
        c.stroke();
        c.fillStyle = "#f59e0b";
        c.font = "11px sans-serif";
        c.fillText("Alarm", xPos + 4, yAxis.top + 14);
        c.restore();
      },
    };

    _chart = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label: "Steam-Preis (EUR)",
            data: points,
            borderWidth: 2,
            tension: 0.25,
            pointRadius: points.length === 1 ? 4 : 0,
            pointHoverRadius: 5,
          },
          ...(buy == null
            ? []
            : [
                {
                  label: "Kaufpreis",
                  data: buyLine,
                  borderWidth: 1,
                  borderDash: [6, 6],
                  pointRadius: 0,
                },
              ]),
        ],
      },
      options: {
        parsing: false,
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: "time",
            time: { unit: "day" },
            grid: { display: false },
          },
          y: {
            ticks: { callback: eurTick },
            grid: { color: "#33415540" },
          },
        },
        plugins: { legend: { display: false } },
      },
      plugins: [triggeredAtPlugin],
    });
  };
})();
