// static/js/chart-helpers.js
(function () {
  let _chart = null;
  let _portfolioChart = null;

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

  window.renderPortfolioChart = function renderPortfolioChart(canvasId, rangeButtonsId, d) {
    const el = document.getElementById(canvasId);
    if (!el) return;

    const ts = Array.isArray(d?.ts) ? d.ts : [];
    const net = Array.isArray(d?.net) ? d.net : [];
    const buy = Array.isArray(d?.buy) ? d.buy : [];
    const allPoints = ts.map((t, i) => ({
      x: t * 1000,
      net: net[i],
      buy: buy[i],
    }));

    function draw(rangeDays) {
      const cutoff = rangeDays > 0 ? Date.now() - rangeDays * 86400000 : 0;
      const pts = allPoints.filter((p) => p.x >= cutoff && Number.isFinite(p.net));
      const netPoints = pts.map((p) => ({ x: p.x, y: p.net }));
      const buyPoints = pts
        .filter((p) => Number.isFinite(p.buy))
        .map((p) => ({ x: p.x, y: p.buy }));

      if (_portfolioChart) {
        try {
          _portfolioChart.destroy();
        } catch (_) {}
        _portfolioChart = null;
      }
      if (!netPoints.length) return;

      _portfolioChart = new Chart(el.getContext("2d"), {
        type: "line",
        data: {
          datasets: [
            {
              label: "Gesamtwert netto (EUR)",
              data: netPoints,
              borderWidth: 2,
              tension: 0.25,
              fill: true,
              backgroundColor: "rgba(125, 211, 252, 0.08)",
              pointRadius: netPoints.length === 1 ? 4 : 0,
              pointHoverRadius: 5,
            },
            ...(buyPoints.length
              ? [
                  {
                    label: "Einsatz (Kaufpreise)",
                    data: buyPoints,
                    borderWidth: 1,
                    borderDash: [6, 6],
                    pointRadius: 0,
                  },
                ]
              : []),
          ],
        },
        options: {
          parsing: false,
          animation: false,
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { type: "time", time: { unit: "day" }, grid: { display: false } },
            y: { ticks: { callback: eurTick }, grid: { color: "#33415540" } },
          },
          plugins: {
            legend: { display: buyPoints.length > 0 },
            tooltip: {
              callbacks: {
                label: (ctx) => ctx.dataset.label + ": " + Number(ctx.parsed.y).toFixed(2) + " EUR",
              },
            },
          },
        },
      });
    }

    const buttonWrap = document.getElementById(rangeButtonsId);
    if (buttonWrap) {
      buttonWrap.querySelectorAll("button[data-range]").forEach((btn) => {
        btn.addEventListener("click", () => {
          buttonWrap
            .querySelectorAll("button[data-range]")
            .forEach((b) => b.classList.remove("nav-active"));
          btn.classList.add("nav-active");
          draw(Number(btn.dataset.range) || 0);
        });
      });
    }

    draw(0);
  };
})();
