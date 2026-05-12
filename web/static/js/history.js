const streamCharts = {
  cards: {},
  power: null,
  current: null,
  voltage: null,
  frequency: null
};

const metricConfig = {
  active_power_avg: {
    label: "Активная мощность",
    unit: "кВт",
    chartId: "stream-power-chart",
    chartKey: "power",
    color: "#3b82f6",
    digits: 2
  },
  current_avg: {
    label: "Ток",
    unit: "A",
    chartId: "stream-current-chart",
    chartKey: "current",
    color: "#10b981",
    digits: 2
  },
  voltage_phase_avg: {
    label: "Напряжение",
    unit: "В",
    chartId: "stream-voltage-chart",
    chartKey: "voltage",
    color: "#f59e0b",
    digits: 1
  },
  frequency: {
    label: "Частота",
    unit: "Гц",
    chartId: "stream-frequency-chart",
    chartKey: "frequency",
    color: "#ef4444",
    digits: 2
  }
};

const meterColors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6"];

function fmtNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toFixed(digits);
}

function fmtTs(ts) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function fetchJSON(url) {
  return fetch(url).then(response => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  });
}

function destroyChart(chart) {
  if (chart) chart.destroy();
}

function metricByName(metrics, name) {
  return metrics.find(item => item.metric === name) || null;
}

function createSparkline(canvas, points, color) {
  return new Chart(canvas, {
    type: "line",
    data: {
      labels: points.map(point => new Date(point.ts * 1000).toLocaleTimeString()),
      datasets: [{
        data: points.map(point => point.value),
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
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { display: false },
        y: { display: false }
      }
    }
  });
}

function renderCards(cards) {
  const container = document.getElementById("stream-cards");
  if (!container) return;

  Object.values(streamCharts.cards).forEach(chart => destroyChart(chart));
  streamCharts.cards = {};

  container.innerHTML = cards.map(card => {
    const rows = Object.keys(metricConfig).map(metricName => {
      const metric = metricByName(card.metrics, metricName);
      const cfg = metricConfig[metricName];
      const canvasId = `stream-card-${card.device_id}-${metricName}`.replaceAll(".", "-");
      const value = metric ? fmtNumber(metric.value, cfg.digits) : "—";
      const minValue = metric ? fmtNumber(metric.min_value, cfg.digits) : "—";
      const maxValue = metric ? fmtNumber(metric.max_value, cfg.digits) : "—";

      return `
        <div class="stream-meter-row">
          <div class="stream-meter-row__label">${cfg.label}</div>
          <div class="stream-meter-row__value">${value} ${cfg.unit}</div>
          <div class="stream-meter-row__chart">
            <canvas id="${canvasId}" class="stream-sparkline"></canvas>
            <div class="stream-meter-row__range">
              <span>max ${maxValue}</span>
              <span>min ${minValue}</span>
            </div>
          </div>
        </div>
      `;
    }).join("");

    return `
      <article class="stream-meter-card">
        <h2 class="stream-meter-card__title">${card.device_id}</h2>
        <div class="stream-meter-card__rows">${rows}</div>
        <div class="stream-meter-card__footer">
          <div>
            <div class="stream-meter-card__footer-label">Последняя точка</div>
            <div class="stream-meter-card__footer-value">${fmtTs(card.last_ts)}</div>
          </div>
          <div>
            <div class="stream-meter-card__footer-label">Источник</div>
            <div class="stream-meter-card__source">
              <span class="source-dot ${card.source_status === "good" ? "source-dot--good" : "source-dot--stale"}"></span>
              ${card.source_status} · ${card.source_name}
            </div>
          </div>
        </div>
      </article>
    `;
  }).join("");

  cards.forEach(card => {
    Object.keys(metricConfig).forEach(metricName => {
      const metric = metricByName(card.metrics, metricName);
      const cfg = metricConfig[metricName];
      const canvasId = `stream-card-${card.device_id}-${metricName}`.replaceAll(".", "-");
      const canvas = document.getElementById(canvasId);
      if (canvas && metric) {
        streamCharts.cards[canvasId] = createSparkline(canvas, metric.sparkline, cfg.color);
      }
    });
  });
}

function chartOptions(unit) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: {
      mode: "nearest",
      intersect: false
    },
    plugins: {
      legend: {
        display: true,
        position: "top",
        labels: {
          boxWidth: 12,
          boxHeight: 12
        }
      },
      tooltip: {
        callbacks: {
          title(items) {
            const ts = items[0]?.parsed?.x;
            return ts ? new Date(ts * 1000).toLocaleString() : "";
          },
          label(item) {
            return `${item.dataset.label}: ${fmtNumber(item.parsed.y, 2)} ${unit}`;
          }
        }
      }
    },
    scales: {
      x: {
        type: "linear",
        grid: { display: false },
        ticks: {
          maxTicksLimit: 8,
          callback(value) {
            return new Date(Number(value) * 1000).toLocaleTimeString();
          }
        }
      },
      y: {
        title: { display: true, text: unit },
        ticks: { maxTicksLimit: 5 }
      }
    }
  };
}

function renderMetricChart(metricName, series) {
  const cfg = metricConfig[metricName];
  const canvas = document.getElementById(cfg.chartId);
  if (!canvas) return;

  destroyChart(streamCharts[cfg.chartKey]);

  const datasets = series
    .filter(item => item.metric === metricName)
    .map((item, index) => ({
      label: item.source_id,
      data: item.points.map(point => ({ x: point.ts, y: point.value })),
      borderColor: meterColors[index % meterColors.length],
      backgroundColor: meterColors[index % meterColors.length],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.18
    }));

  streamCharts[cfg.chartKey] = new Chart(canvas, {
    type: "line",
    data: { datasets },
    options: chartOptions(cfg.unit)
  });
}

function renderSeries(response) {
  document.getElementById("stream-chart-reference").textContent = fmtTs(response.reference_ts);
  Object.keys(metricConfig).forEach(metricName => {
    renderMetricChart(metricName, response.series);
  });
}

async function loadRealtime() {
  const realtime = await fetchJSON("/api/history/realtime");
  renderCards(realtime.cards);

  const series = await fetchJSON("/api/history/series?mode=online");
  renderSeries(series);
}

function buildHistoryQuery() {
  const year = document.getElementById("history-year-select").value || "";
  const month = document.getElementById("history-month-select").value || "";
  const day = document.getElementById("history-day-select").value || "";
  const aggregation = document.getElementById("history-aggregation-select").value || "5";
  const qs = new URLSearchParams({ mode: "historical", aggregation_min: aggregation });

  if (year) qs.set("year", year);
  if (month) qs.set("month", month);
  if (day) qs.set("day", day);

  return qs.toString();
}

async function loadHistorical() {
  const onlineBtn = document.getElementById("stream-online-btn");
  onlineBtn.classList.remove("active");

  const series = await fetchJSON(`/api/history/series?${buildHistoryQuery()}`);
  renderSeries(series);
}

document.addEventListener("DOMContentLoaded", async () => {
  const onlineBtn = document.getElementById("stream-online-btn");
  const runBtn = document.getElementById("history-run-btn");

  onlineBtn.addEventListener("click", async () => {
    onlineBtn.classList.add("active");
    await loadRealtime();
  });

  runBtn.addEventListener("click", loadHistorical);

  await loadRealtime();

  setInterval(() => {
    if (onlineBtn.classList.contains("active")) {
      loadRealtime();
    }
  }, 10000);
});
