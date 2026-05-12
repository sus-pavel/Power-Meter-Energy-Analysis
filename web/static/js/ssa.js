function fmtNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toFixed(digits);
}

function fetchJSON(url) {
  return fetch(url).then(response => {
    if (!response.ok) {
      return response.json().catch(() => ({})).then(payload => {
        throw new Error(payload.detail || `HTTP ${response.status}`);
      });
    }
    return response.json();
  });
}

const ssaPlotIds = [
  "ssa-original-plot",
  "ssa-wcorr-plot",
  "ssa-cumulative-plot",
  "ssa-scatter-plot",
  "ssa-grouped-plot",
  "ssa-components-plot",
  "ssa-clusters-plot"
];

function escapeHTML(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderEmptyState(targetId, title, text) {
  const target = document.getElementById(targetId);
  if (!target) return;
  Plotly.purge(target);
  target.innerHTML = `
    <div class="empty-state">
      <div class="empty-state__inner">
        <p class="empty-state__title">${escapeHTML(title)}</p>
        <p class="empty-state__text">${escapeHTML(text)}</p>
      </div>
    </div>
  `;
}

function renderAllEmptyStates(title, text) {
  ssaPlotIds.forEach(id => renderEmptyState(id, title, text));
}

function selectedMeters() {
  return Array.from(document.querySelectorAll(".ssa-meter-checkbox:checked")).map(node => node.value);
}

function syncWindowHours() {
  const aggMin = Number(document.getElementById("ssa-aggregation-min").value || 0);
  const windowPoints = Number(document.getElementById("ssa-window-points").value || 0);
  const hours = aggMin && windowPoints ? (aggMin * windowPoints) / 60 : 0;
  document.getElementById("ssa-window-hours").textContent =
    hours ? `Размер окна: ${fmtNumber(hours, 2)} ч` : "—";
}

function buildQuery() {
  const qs = new URLSearchParams();
  selectedMeters().forEach(value => qs.append("device_ids", value));
  qs.set("start_at", document.getElementById("ssa-start-at").value);
  qs.set("end_at", document.getElementById("ssa-end-at").value);
  qs.set("aggregation_min", document.getElementById("ssa-aggregation-min").value);
  qs.set("window_points", document.getElementById("ssa-window-points").value);
  qs.set("component_count", document.getElementById("ssa-component-count").value);
  qs.set("cluster_count", document.getElementById("ssa-cluster-count").value);
  return qs.toString();
}

function updateSummary(summary) {
  document.getElementById("ssa-summary-object").textContent = summary.analysis_object || "—";
  document.getElementById("ssa-summary-start").textContent = summary.start_at || "—";
  document.getElementById("ssa-summary-end").textContent = summary.end_at || "—";
  document.getElementById("ssa-summary-components").textContent = `${summary.component_count} / ${summary.cluster_count}`;
  document.getElementById("ssa-status").textContent =
    `Точек: ${summary.sample_count} · agg ${summary.aggregation_min} мин · окно ${fmtNumber(summary.window_hours, 2)} ч`;
}

function lineTrace(series, extra = {}) {
  return {
    type: "scatter",
    mode: "lines",
    name: series.label,
    x: series.points.map(point => new Date(point.ts * 1000)),
    y: series.points.map(point => point.value),
    line: { color: series.color, width: extra.width || 2 },
    opacity: extra.opacity || 1,
    ...extra
  };
}

function baseLayout(yTitle) {
  return {
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    margin: { l: 56, r: 24, t: 24, b: 56 },
    xaxis: {
      title: "Дата",
      gridcolor: "#e8edf5",
      zeroline: false
    },
    yaxis: {
      title: yTitle,
      gridcolor: "#e8edf5",
      zeroline: false
    },
    legend: {
      orientation: "h",
      yanchor: "bottom",
      y: 1.02,
      xanchor: "left",
      x: 0
    }
  };
}

function renderOriginalPlot(points) {
  Plotly.react("ssa-original-plot", [{
    type: "scatter",
    mode: "lines",
    name: "Исходный ряд",
    x: points.map(point => new Date(point.ts * 1000)),
    y: points.map(point => point.value),
    line: { color: "#2563eb", width: 3 }
  }], baseLayout("Мощность, кВт"), { responsive: true, displayModeBar: false });
}

function renderWcorr(matrix) {
  const size = matrix.length;
  const labels = Array.from({ length: size }, (_, index) => `RC${index + 1}`);
  Plotly.react("ssa-wcorr-plot", [{
    type: "heatmap",
    z: matrix,
    x: labels,
    y: labels,
    colorscale: "RdBu",
    reversescale: false,
    zmin: 0,
    zmax: 1,
    colorbar: { title: "" }
  }], {
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    margin: { l: 56, r: 24, t: 24, b: 48 }
  }, { responsive: true, displayModeBar: false });
}

function renderCumulative(points) {
  Plotly.react("ssa-cumulative-plot", [{
    type: "scatter",
    mode: "lines+markers",
    name: "Кумулятивный вклад",
    x: points.map(point => `RC${point.component}`),
    y: points.map(point => point.cumulative),
    line: { color: "#2563eb", width: 3 },
    marker: { color: "#2563eb", size: 8 }
  }], {
    ...baseLayout("Доля"),
    xaxis: { title: "Компонента", gridcolor: "#e8edf5", zeroline: false }
  }, { responsive: true, displayModeBar: false });
}

function renderScatter(points) {
  const clusters = [...new Set(points.map(point => point.cluster))].sort((a, b) => a - b);
  const traces = clusters.map(cluster => {
    const clusterPoints = points.filter(point => point.cluster === cluster);
    return {
      type: "scatter",
      mode: "markers",
      name: `Cluster ${cluster}`,
      x: clusterPoints.map(point => point.frequency),
      y: clusterPoints.map(point => point.amplitude),
      text: clusterPoints.map(point => `RC${point.component}`),
      marker: {
        color: clusterPoints[0]?.color || "#2563eb",
        size: 10
      }
    };
  });

  Plotly.react("ssa-scatter-plot", traces, {
    ...baseLayout("Амплитуда"),
    xaxis: { title: "Частота", gridcolor: "#e8edf5", zeroline: false }
  }, { responsive: true, displayModeBar: false });
}

function renderGrouped(series) {
  Plotly.react(
    "ssa-grouped-plot",
    series.map((item, index) => lineTrace(item, { width: index === 0 ? 3 : 2 })),
    baseLayout("Значение"),
    { responsive: true, displayModeBar: false }
  );
}

function renderComponents(series) {
  Plotly.react(
    "ssa-components-plot",
    series.map(item => lineTrace(item, { width: item.label === "RC1" ? 3 : 1.8 })),
    baseLayout("Компоненты"),
    { responsive: true, displayModeBar: false }
  );
}

function renderClusters(series) {
  Plotly.react(
    "ssa-clusters-plot",
    series.map(item => lineTrace(item)),
    baseLayout("Значение"),
    { responsive: true, displayModeBar: false }
  );
}

function renderAnalysis(response) {
  updateSummary(response.summary);
  renderOriginalPlot(response.original_series);
  renderWcorr(response.wcorr);
  renderCumulative(response.cumulative_contribution);
  renderScatter(response.amplitude_frequency);
  renderGrouped(response.grouped_series);
  renderComponents(response.component_series);
  renderClusters(response.cluster_series);
}

async function runSSA() {
  const meters = selectedMeters();
  if (!meters.length) {
    document.getElementById("ssa-status").textContent = "Выбери хотя бы один счётчик.";
    renderAllEmptyStates("Не выбран счётчик", "Отметьте один или несколько счётчиков и запустите расчёт.");
    return;
  }

  document.getElementById("ssa-status").textContent = "Идёт расчёт...";
  renderAllEmptyStates("Расчёт SSA", "Подготавливаем временной ряд и диагностические графики.");

  try {
    const response = await fetchJSON(`/api/ssa/analyze?${buildQuery()}`);
    renderAnalysis(response);
  } catch (error) {
    const message = error.message || "Не удалось выполнить SSA-анализ";
    document.getElementById("ssa-status").textContent = message;
    renderAllEmptyStates(
      "Недостаточно данных для анализа",
      `${message}. Увеличьте период анализа, уменьшите размер агрегации или дождитесь накопления новых измерений.`
    );
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  syncWindowHours();

  document.getElementById("ssa-aggregation-min").addEventListener("change", syncWindowHours);
  document.getElementById("ssa-window-points").addEventListener("input", syncWindowHours);
  document.getElementById("ssa-run-btn").addEventListener("click", runSSA);
  document.getElementById("ssa-run-btn-header").addEventListener("click", runSSA);

  await runSSA();
});
