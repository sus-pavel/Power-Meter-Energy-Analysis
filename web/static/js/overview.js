let overviewCharts = {
  drpiSparkline: null,
  powerSparkline: null,
  meterCharts: {}
};

function fmtNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(digits);
}

function unixToLocale(ts) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function destroyChart(chart) {
  if (chart) {
    chart.destroy();
  }
}

function chartCommonOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: { display: false }
    },
    scales: {
      x: { display: false },
      y: { display: false }
    }
  };
}

function createSparkline(canvasId, points, label, color = "#2563eb") {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: points.map(p => new Date(p.ts * 1000).toLocaleTimeString()),
      datasets: [{
        label,
        data: points.map(p => p.value),
        borderColor: color,
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.25
      }]
    },
    options: chartCommonOptions()
  });
}

function createMeterChart(canvasId, series, color = "#2563eb") {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: series.points.map(p => new Date(p.ts * 1000).toLocaleTimeString()),
      datasets: [{
        label: series.source_id,
        data: series.points.map(p => p.value),
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
        y: { display: true }
      }
    }
  });
}

function colorForHeatmap(value, min, max) {
  if (value === null || value === undefined) return "#eef1f5";

  const ratio = (value - min) / ((max - min) || 1);
  const r = 255;
  const g = Math.round(245 - ratio * 100);
  const b = Math.round(220 - ratio * 180);
  return `rgb(${r}, ${g}, ${b})`;
}

function renderHeatmap(containerId, cells) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const values = cells.map(c => c.value).filter(v => v !== null);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;

  const weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

  let html = `<div class="heatmap-grid">`;
  html += `<div class="heatmap-header"></div>`;

  for (let h = 0; h < 24; h++) {
    html += `<div class="heatmap-header">${String(h).padStart(2, "0")}:00</div>`;
  }

  for (let wd = 0; wd < 7; wd++) {
    html += `<div class="heatmap-side">${weekdays[wd]}</div>`;

    for (let h = 0; h < 24; h++) {
      const cell = cells.find(c => c.weekday === wd && c.hour === h);
      const value = cell ? cell.value : null;
      const color = colorForHeatmap(value, min, max);
      const text = value === null ? "—" : Number(value).toFixed(2);

      html += `
        <div class="heatmap-cell" style="background:${color}">
          ${text}
        </div>
      `;
    }
  }

  html += `</div>`;
  container.innerHTML = html;
}

async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await response.json();
}

function getParams() {
  const mode = document.getElementById("mode-online-btn").classList.contains("active")
    ? "online"
    : "historical";

  const year = document.getElementById("year-select").value || "";
  const month = document.getElementById("month-select").value || "";

  const qs = new URLSearchParams({ mode });
  if (year) qs.set("year", year);
  if (month) qs.set("month", month);

  return qs.toString();
}

async function loadOverview() {
  const qs = getParams();

  const summary = await fetchJSON(`/api/overview/summary?${qs}`);
  document.getElementById("overview-current-drpi").textContent = fmtNumber(summary.current_drpi, 2);
  document.getElementById("overview-total-power").textContent = fmtNumber(summary.current_total_power_kw, 2);
  document.getElementById("overview-active-meters").textContent = `${summary.active_meters} / ${summary.total_meters}`;
  document.getElementById("overview-reference-ts").textContent = unixToLocale(summary.reference_ts);

  destroyChart(overviewCharts.drpiSparkline);
  overviewCharts.drpiSparkline = createSparkline(
    "overview-drpi-sparkline",
    summary.drpi_sparkline,
    "DRPI",
    "#f59e0b"
  );

  destroyChart(overviewCharts.powerSparkline);
  overviewCharts.powerSparkline = createSparkline(
    "overview-power-sparkline",
    summary.total_power_sparkline,
    "Power",
    "#60a5fa"
  );

  const powerMeters = await fetchJSON(`/api/overview/power-meters?${qs}`);

  for (let i = 1; i <= 4; i++) {
    if (overviewCharts.meterCharts[i]) {
      destroyChart(overviewCharts.meterCharts[i]);
      overviewCharts.meterCharts[i] = null;
    }
  }

  powerMeters.series.forEach((series, idx) => {
    const chartIndex = idx + 1;
    overviewCharts.meterCharts[chartIndex] = createMeterChart(
      `meter-chart-${chartIndex}`,
      series
    );
  });

  const heatmap = await fetchJSON(`/api/overview/drpi-heatmap?source_id=TOTAL&${qs}`);
  renderHeatmap("overview-heatmap-container", heatmap.cells);
}

document.addEventListener("DOMContentLoaded", async () => {
  const onlineBtn = document.getElementById("mode-online-btn");
  const yearSelect = document.getElementById("year-select");
  const monthSelect = document.getElementById("month-select");

  onlineBtn.addEventListener("click", () => {
    onlineBtn.classList.toggle("active");
    if (onlineBtn.classList.contains("active")) {
      yearSelect.value = "";
      monthSelect.value = "";
    }
    loadOverview();
  });

  yearSelect.addEventListener("change", () => {
    onlineBtn.classList.remove("active");
    loadOverview();
  });

  monthSelect.addEventListener("change", () => {
    onlineBtn.classList.remove("active");
    loadOverview();
  });

  await loadOverview();

  setInterval(() => {
    if (onlineBtn.classList.contains("active")) {
      loadOverview();
    }
  }, 15000);
});