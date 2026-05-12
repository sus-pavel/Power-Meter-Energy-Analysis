const drpiCharts = {};

function fmtNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(digits);
}

function fetchJSON(url) {
  return fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });
}

function getParams() {
  const sourceId = document.getElementById("meter-select").value || "TOTAL";
  const mode = document.getElementById("mode-online-btn").classList.contains("active") ? "online" : "historical";
  const year = document.getElementById("year-select").value || "";
  const month = document.getElementById("month-select").value || "";

  const qs = new URLSearchParams({ source_id: sourceId, mode });
  if (year) qs.set("year", year);
  if (month) qs.set("month", month);
  return qs.toString();
}

function makeLineChart(canvasId, seriesList) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  if (drpiCharts[canvasId]) {
    drpiCharts[canvasId].destroy();
  }

  const hasPoints = seriesList.some(s => s.points && s.points.length);
  const parent = ctx.parentElement;
  const oldEmptyState = parent?.querySelector(".chart-empty-state");
  if (oldEmptyState) oldEmptyState.remove();

  if (!hasPoints) {
    ctx.style.display = "none";
    if (parent) {
      parent.insertAdjacentHTML(
        "beforeend",
        '<div class="chart-empty-state">Нет точек для построения графика в выбранном периоде.</div>'
      );
    }
    return null;
  }

  ctx.style.display = "block";

  drpiCharts[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels: seriesList[0]?.points?.map(p => new Date(p.ts * 1000).toLocaleString()) || [],
      datasets: seriesList.map(s => ({
        label: s.label,
        data: s.points.map(p => p.value),
        borderColor: s.color,
        backgroundColor: s.color,
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.2,
        spanGaps: true
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          display: seriesList.length > 1,
          position: "top",
          labels: {
            boxWidth: 12,
            boxHeight: 12,
            font: { weight: "700" }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxTicksLimit: 8 }
        },
        y: {
          grid: { color: "#e8edf4" },
          ticks: { maxTicksLimit: 6 }
        }
      }
    }
  });

  return drpiCharts[canvasId];
}

function makeSparkline(canvasId, points, color) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  if (drpiCharts[canvasId]) {
    drpiCharts[canvasId].destroy();
  }

  if (!points || !points.length) {
    ctx.style.display = "none";
    return null;
  }

  ctx.style.display = "block";

  drpiCharts[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels: points.map(p => new Date(p.ts * 1000).toLocaleTimeString()),
      datasets: [{
        data: points.map(p => p.value),
        borderColor: color,
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { display: false },
        y: { display: false }
      }
    }
  });

  return drpiCharts[canvasId];
}

async function loadDRPI() {
  const qs = getParams();

  const summary = await fetchJSON(`/api/drpi/summary?${qs}`);
  document.getElementById("drpi-current-value").textContent = fmtNumber(summary.current_drpi, 2);
  document.getElementById("drpi-best-days").textContent = summary.preferred_days.length ? summary.preferred_days.join(", ") : "—";
  document.getElementById("drpi-min-max").textContent =
    summary.min_24h !== null && summary.max_24h !== null
      ? `${fmtNumber(summary.min_24h, 2)} → ${fmtNumber(summary.max_24h, 2)}`
      : "—";

  document.getElementById("drpi-f1-value").textContent = fmtNumber(summary.current_f1, 2);
  document.getElementById("drpi-f2-value").textContent = fmtNumber(summary.current_f2, 2);
  document.getElementById("drpi-f3-value").textContent = fmtNumber(summary.current_f3, 2);

  makeSparkline("drpi-f1-sparkline", summary.sparkline_f1, "#10b981");
  makeSparkline("drpi-f2-sparkline", summary.sparkline_f2, "#f59e0b");
  makeSparkline("drpi-f3-sparkline", summary.sparkline_f3, "#8b5cf6");

  const history = await fetchJSON(`/api/drpi/history?${qs}`);
  makeLineChart("drpi-history-chart", [
    {
      label: "DRPI",
      color: "#2563eb",
      points: history.drpi
    }
  ]);

  const components = await fetchJSON(`/api/drpi/components?${qs}`);
  makeLineChart("drpi-components-chart", [
    { label: "F1", color: "#10b981", points: components.f1 },
    { label: "F2", color: "#f59e0b", points: components.f2 },
    { label: "F3", color: "#8b5cf6", points: components.f3 }
  ]);
}

document.addEventListener("DOMContentLoaded", async () => {
  const onlineBtn = document.getElementById("mode-online-btn");
  const yearSelect = document.getElementById("year-select");
  const monthSelect = document.getElementById("month-select");
  const meterSelect = document.getElementById("meter-select");

  onlineBtn.addEventListener("click", () => {
    onlineBtn.classList.toggle("active");
    if (onlineBtn.classList.contains("active")) {
      yearSelect.value = "";
      monthSelect.value = "";
    }
    loadDRPI();
  });

  yearSelect.addEventListener("change", () => {
    onlineBtn.classList.remove("active");
    loadDRPI();
  });

  monthSelect.addEventListener("change", () => {
    onlineBtn.classList.remove("active");
    loadDRPI();
  });

  meterSelect.addEventListener("change", loadDRPI);

  await loadDRPI();

  setInterval(() => {
    if (onlineBtn.classList.contains("active")) {
      loadDRPI();
    }
  }, 30000);
});
