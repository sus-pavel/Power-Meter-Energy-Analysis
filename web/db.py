from __future__ import annotations

import calendar
import sqlite3
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core.ssa_engine import SSADecomposer, SSAKMeansClusterer
from web.schemas import (
    SSAAnalysisResponse,
    SSACumulativePoint,
    SSALineSeries,
    SSAScatterPoint,
    SSASummaryResponse,
    DRPIComponentsResponse,
    DRPIHistoryResponse,
    DRPISummaryResponse,
    HeatmapCell,
    OverviewHeatmapResponse,
    OverviewPowerMetersResponse,
    OverviewSummaryResponse,
    SelectOption,
    SeriesResponse,
    SparklinePoint,
    StreamChartSeries,
    StreamMeterCard,
    StreamMetricSnapshot,
    StreamRealtimeResponse,
    StreamSeriesResponse,
    TimeSeriesPoint,
)

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "energy.db"

STREAM_METRICS = {
    "active_power_avg": {
        "label": "Активная мощность",
        "short_label": "Активная мощность",
        "unit": "кВт",
        "color": "#3b82f6",
    },
    "current_avg": {
        "label": "Ток",
        "short_label": "Ток",
        "unit": "A",
        "color": "#10b981",
    },
    "voltage_phase_avg": {
        "label": "Напряжение",
        "short_label": "Напряжение",
        "unit": "В",
        "color": "#f59e0b",
    },
    "frequency": {
        "label": "Частота",
        "short_label": "Частота",
        "unit": "Гц",
        "color": "#ef4444",
    },
}

STREAM_AGG_TABLES = {
    5: "agg_5min",
    10: "agg_10min",
    15: "agg_15min",
    30: "agg_30min",
    60: "agg_1h",
}

SSA_COLORS = [
    "#2563eb",
    "#60a5fa",
    "#ef4444",
    "#fca5a5",
    "#14b8a6",
    "#22c55e",
    "#f59e0b",
    "#fbbf24",
    "#7c3aed",
    "#94a3b8",
    "#0ea5e9",
    "#38bdf8",
    "#ec4899",
    "#10b981",
    "#6366f1",
    "#84cc16",
    "#fb7185",
    "#06b6d4",
    "#a855f7",
    "#8b5cf6",
]


# =========================
# Low-level helpers
# =========================

def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = str(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def to_unix_month_bounds(year: int, month: int) -> tuple[int, int]:
    start_tuple = (year, month, 1, 0, 0, 0, 0, 0, -1)
    start_ts = int(time.mktime(start_tuple))
    last_day = calendar.monthrange(year, month)[1]
    end_tuple = (year, month, last_day, 23, 59, 59, 0, 0, -1)
    end_ts = int(time.mktime(end_tuple))
    return start_ts, end_ts + 1


def to_unix_day_bounds(year: int, month: int, day: int) -> tuple[int, int]:
    start_tuple = (year, month, day, 0, 0, 0, 0, 0, -1)
    end_tuple = (year, month, day, 23, 59, 59, 0, 0, -1)
    return int(time.mktime(start_tuple)), int(time.mktime(end_tuple)) + 1


def query_scalar(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> Any:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return None
    return row[0]


def get_latest_ts(conn: sqlite3.Connection, table_name: str, column_name: str) -> int | None:
    value = query_scalar(conn, f"SELECT MAX({column_name}) FROM {table_name}")
    return int(value) if value is not None else None


def get_available_year_months_from_table(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> tuple[list[int], list[int]]:
    rows = conn.execute(
        f"""
        SELECT DISTINCT strftime('%Y', datetime({column_name}, 'unixepoch')) AS year,
                        strftime('%m', datetime({column_name}, 'unixepoch')) AS month
        FROM {table_name}
        WHERE {column_name} IS NOT NULL
        ORDER BY year, month
        """
    ).fetchall()

    years = sorted({int(r["year"]) for r in rows if r["year"] is not None})
    months = sorted({int(r["month"]) for r in rows if r["month"] is not None})
    return years, months


def build_time_filter(
    mode: str,
    ts_column: str,
    year: int | None,
    month: int | None,
    default_online_lookback_sec: int | None = None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if mode == "historical" and year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)
        clauses.append(f"{ts_column} >= ?")
        clauses.append(f"{ts_column} < ?")
        params.extend([start_ts, end_ts])
    elif mode == "online" and default_online_lookback_sec is not None:
        latest_bound = int(time.time()) - default_online_lookback_sec
        clauses.append(f"{ts_column} >= ?")
        params.append(latest_bound)

    where_sql = ""
    if clauses:
        where_sql = " AND " + " AND ".join(clauses)

    return where_sql, params


# =========================
# Common option data
# =========================

def get_meter_options(conn: sqlite3.Connection) -> list[SelectOption]:
    rows = conn.execute(
        """
        SELECT DISTINCT source_id AS meter_id
        FROM drpi_results
        WHERE source_id != 'TOTAL'
        ORDER BY source_id
        """
    ).fetchall()

    options = [SelectOption(value="TOTAL", label="TOTAL")]
    options.extend(SelectOption(value=r["meter_id"], label=r["meter_id"]) for r in rows)
    return options


def get_year_month_options(conn: sqlite3.Connection) -> tuple[list[int], list[int]]:
    years_1, months_1 = get_available_year_months_from_table(conn, "drpi_results", "ts")
    years_2, months_2 = get_available_year_months_from_table(conn, "raw_data", "timestamp")

    years = sorted(set(years_1) | set(years_2))
    months = sorted(set(months_1) | set(months_2))
    return years, months


def get_day_options(conn: sqlite3.Connection, year: int | None = None, month: int | None = None) -> list[int]:
    where_sql = ""
    params: list[Any] = []

    if year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)
        where_sql = "WHERE timestamp >= ? AND timestamp < ?"
        params.extend([start_ts, end_ts])

    rows = conn.execute(
        f"""
        SELECT DISTINCT strftime('%d', datetime(timestamp, 'unixepoch')) AS day
        FROM raw_data
        {where_sql}
        ORDER BY day
        """,
        tuple(params),
    ).fetchall()

    return [int(r["day"]) for r in rows if r["day"] is not None]


# =========================
# Realtime stream / history
# =========================

def metric_info(metric: str) -> dict[str, str]:
    return STREAM_METRICS.get(
        metric,
        {
            "label": metric,
            "short_label": metric,
            "unit": "",
            "color": "#64748b",
        },
    )


def get_stream_realtime(
    conn: sqlite3.Connection,
    horizon_sec: int = 180,
    stale_after_sec: int = 30,
) -> StreamRealtimeResponse:
    latest_ts = get_latest_ts(conn, "raw_data", "timestamp")
    if latest_ts is None:
        return StreamRealtimeResponse(cards=[], reference_ts=None)

    device_rows = conn.execute(
        """
        SELECT DISTINCT device_id
        FROM raw_data
        WHERE metric = 'active_power_avg'
        ORDER BY device_id
        """
    ).fetchall()

    metric_names = list(STREAM_METRICS.keys())
    cards: list[StreamMeterCard] = []

    for device_row in device_rows:
        device_id = str(device_row["device_id"])
        metric_snapshots: list[StreamMetricSnapshot] = []
        device_last_ts: int | None = None

        for metric_name in metric_names:
            latest_row = conn.execute(
                """
                SELECT timestamp, value
                FROM raw_data
                WHERE device_id = ?
                  AND metric = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (device_id, metric_name),
            ).fetchone()

            range_row = conn.execute(
                """
                SELECT MIN(value) AS min_value,
                       MAX(value) AS max_value
                FROM raw_data
                WHERE device_id = ?
                  AND metric = ?
                  AND timestamp >= ?
                """,
                (device_id, metric_name, int(latest_ts) - horizon_sec),
            ).fetchone()

            spark_rows = conn.execute(
                """
                SELECT CAST(timestamp / 5 AS INTEGER) * 5 AS ts,
                       AVG(value) AS value
                FROM raw_data
                WHERE device_id = ?
                  AND metric = ?
                  AND timestamp >= ?
                GROUP BY ts
                ORDER BY ts
                """,
                (device_id, metric_name, int(latest_ts) - horizon_sec),
            ).fetchall()

            info = metric_info(metric_name)
            if latest_row is not None:
                device_last_ts = max(
                    device_last_ts or 0,
                    int(float(latest_row["timestamp"])),
                )

            metric_snapshots.append(
                StreamMetricSnapshot(
                    metric=metric_name,
                    label=info["short_label"],
                    unit=info["unit"],
                    value=float(latest_row["value"]) if latest_row is not None else None,
                    min_value=float(range_row["min_value"]) if range_row and range_row["min_value"] is not None else None,
                    max_value=float(range_row["max_value"]) if range_row and range_row["max_value"] is not None else None,
                    sparkline=[
                        SparklinePoint(ts=int(r["ts"]), value=float(r["value"]))
                        for r in spark_rows
                    ],
                )
            )

        status = "good" if device_last_ts is not None and device_last_ts >= int(latest_ts) - stale_after_sec else "stale"
        cards.append(
            StreamMeterCard(
                device_id=device_id,
                metrics=metric_snapshots,
                last_ts=device_last_ts,
                source_status=status,
                source_name="kepware",
            )
        )

    return StreamRealtimeResponse(cards=cards, reference_ts=int(latest_ts))


def get_stream_series(
    conn: sqlite3.Connection,
    mode: str,
    year: int | None,
    month: int | None,
    day: int | None,
    aggregation_min: int | None,
) -> StreamSeriesResponse:
    metric_names = list(STREAM_METRICS.keys())
    series_by_key: dict[tuple[str, str], list[TimeSeriesPoint]] = {}
    reference_ts: int | None = None

    if mode == "historical" and not (year and month and day):
        return StreamSeriesResponse(
            mode="historical",
            year=year,
            month=month,
            day=day,
            aggregation_min=aggregation_min if aggregation_min in STREAM_AGG_TABLES else 5,
            series=[],
            reference_ts=None,
        )

    if mode == "historical" and year and month and day:
        agg_min = aggregation_min if aggregation_min in STREAM_AGG_TABLES else 5
        table_name = STREAM_AGG_TABLES[agg_min]
        start_ts, end_ts = to_unix_day_bounds(year, month, day)
        placeholders = ",".join("?" for _ in metric_names)

        rows = conn.execute(
            f"""
            SELECT window_end AS ts,
                   device_id,
                   metric,
                   mean_value AS value
            FROM {table_name}
            WHERE metric IN ({placeholders})
              AND window_end >= ?
              AND window_end < ?
            ORDER BY device_id, metric, window_end
            """,
            tuple([*metric_names, start_ts, end_ts]),
        ).fetchall()

        agg_for_response: int | None = agg_min
    else:
        start_ts = int(time.time()) - 3600
        placeholders = ",".join("?" for _ in metric_names)
        rows = conn.execute(
            f"""
            SELECT CAST(timestamp / 10 AS INTEGER) * 10 AS ts,
                   device_id,
                   metric,
                   AVG(value) AS value
            FROM raw_data
            WHERE metric IN ({placeholders})
              AND timestamp >= ?
            GROUP BY ts, device_id, metric
            ORDER BY device_id, metric, ts
            """,
            tuple([*metric_names, start_ts]),
        ).fetchall()
        agg_for_response = None

    for row in rows:
        source_id = str(row["device_id"])
        metric_name = str(row["metric"])
        ts = int(row["ts"])
        value = float(row["value"])
        reference_ts = max(reference_ts or 0, ts)
        series_by_key.setdefault((source_id, metric_name), []).append(
            TimeSeriesPoint(ts=ts, value=value)
        )

    chart_series: list[StreamChartSeries] = []
    for (source_id, metric_name), points in sorted(series_by_key.items()):
        info = metric_info(metric_name)
        chart_series.append(
            StreamChartSeries(
                source_id=source_id,
                metric=metric_name,
                label=f"{source_id} · {info['label']}",
                unit=info["unit"],
                color=info["color"],
                points=points,
            )
        )

    return StreamSeriesResponse(
        mode="historical" if mode == "historical" else "online",
        year=year,
        month=month,
        day=day,
        aggregation_min=agg_for_response,
        series=chart_series,
        reference_ts=reference_ts,
    )


# =========================
# SSA analysis
# =========================

def get_raw_meter_options(conn: sqlite3.Connection) -> list[SelectOption]:
    rows = conn.execute(
        """
        SELECT DISTINCT device_id
        FROM raw_data
        WHERE metric = 'active_power_avg'
        ORDER BY device_id
        """
    ).fetchall()
    return [SelectOption(value=str(r["device_id"]), label=str(r["device_id"])) for r in rows]


def get_agg_time_bounds(conn: sqlite3.Connection, aggregation_min: int) -> tuple[int | None, int | None]:
    table_name = STREAM_AGG_TABLES.get(aggregation_min)
    if table_name is None:
        return None, None

    row = conn.execute(
        f"""
        SELECT MIN(window_end) AS min_ts,
               MAX(window_end) AS max_ts
        FROM {table_name}
        WHERE metric = 'active_power_avg'
        """
    ).fetchone()

    if row is None:
        return None, None

    min_ts = int(row["min_ts"]) if row["min_ts"] is not None else None
    max_ts = int(row["max_ts"]) if row["max_ts"] is not None else None
    return min_ts, max_ts


def format_ts_local(ts: int | None) -> str:
    if ts is None:
        return ""
    return time.strftime("%Y-%m-%dT%H:%M", time.localtime(ts))


def get_ssa_page_defaults(conn: sqlite3.Connection, aggregation_min: int = 30) -> dict[str, Any]:
    min_ts, max_ts = get_agg_time_bounds(conn, aggregation_min)

    if max_ts is None:
        return {
            "start_at": "",
            "end_at": "",
            "aggregation_min": aggregation_min,
            "window_points": 48,
            "component_count": 20,
            "cluster_count": 4,
        }

    default_end = max_ts
    default_start = max(min_ts or max_ts, max_ts - 7 * 24 * 3600)

    return {
        "start_at": format_ts_local(default_start),
        "end_at": format_ts_local(default_end),
        "aggregation_min": aggregation_min,
        "window_points": 48,
        "component_count": 20,
        "cluster_count": 4,
    }


def parse_local_datetime(value: str) -> int:
    return int(time.mktime(time.strptime(value, "%Y-%m-%dT%H:%M")))


def get_ssa_series_for_analysis(
    conn: sqlite3.Connection,
    device_ids: list[str],
    start_at: str,
    end_at: str,
    aggregation_min: int,
) -> pd.Series:
    if not device_ids:
        raise ValueError("Не выбраны счётчики для анализа")

    table_name = STREAM_AGG_TABLES.get(aggregation_min)
    if table_name is None:
        raise ValueError("Неподдерживаемый размер агрегации")

    start_ts = parse_local_datetime(start_at)
    end_ts = parse_local_datetime(end_at)
    if end_ts <= start_ts:
        raise ValueError("Дата окончания должна быть позже даты начала")

    placeholders = ",".join("?" for _ in device_ids)
    rows = conn.execute(
        f"""
        SELECT window_end AS ts,
               device_id,
               mean_value
        FROM {table_name}
        WHERE metric = 'active_power_avg'
          AND device_id IN ({placeholders})
          AND window_end >= ?
          AND window_end <= ?
        ORDER BY window_end, device_id
        """,
        tuple([*device_ids, start_ts, end_ts]),
    ).fetchall()

    if not rows:
        raise ValueError("За выбранный период нет агрегированных данных")

    df = pd.DataFrame(
        {
            "ts": [int(r["ts"]) for r in rows],
            "device_id": [str(r["device_id"]) for r in rows],
            "value": [float(r["mean_value"]) for r in rows],
        }
    )

    pivot = df.pivot_table(index="ts", columns="device_id", values="value", aggfunc="mean").sort_index()

    missing_devices = [device_id for device_id in device_ids if device_id not in pivot.columns]
    if missing_devices:
        raise ValueError(f"Нет данных для счётчиков: {', '.join(missing_devices)}")

    if len(device_ids) == 1:
        series = pivot[device_ids[0]].dropna()
    else:
        series = pivot[device_ids].sum(axis=1, min_count=len(device_ids)).dropna()

    if series.empty:
        raise ValueError("Недостаточно полных точек для выбранной группы счётчиков")

    series.index = pd.to_datetime(series.index, unit="s")
    return series.astype(float)


def ts_points_from_series(series: pd.Series | np.ndarray, index: pd.Index) -> list[TimeSeriesPoint]:
    values = np.asarray(series, dtype=float)
    return [
        TimeSeriesPoint(ts=int(pd.Timestamp(ts).timestamp()), value=float(value))
        for ts, value in zip(index, values, strict=False)
    ]


def analyze_ssa(
    conn: sqlite3.Connection,
    device_ids: list[str],
    start_at: str,
    end_at: str,
    aggregation_min: int,
    window_points: int,
    component_count: int,
    cluster_count: int,
) -> SSAAnalysisResponse:
    ts = get_ssa_series_for_analysis(
        conn=conn,
        device_ids=device_ids,
        start_at=start_at,
        end_at=end_at,
        aggregation_min=aggregation_min,
    )

    if len(ts) <= 4:
        raise ValueError("Недостаточно точек для SSA-анализа")

    window_points = max(2, min(int(window_points), len(ts) - 1))
    component_count = max(2, min(int(component_count), len(ts) - 1))
    cluster_count = max(1, int(cluster_count))
    fs = max(1, int(round(1440 / aggregation_min)))

    decomposer = SSADecomposer(ts, window_size=window_points)
    ssa_result = decomposer.fit()

    clusterer = SSAKMeansClusterer(
        fs=fs,
        n_clusters=cluster_count,
        random_state=42,
        n_init=10,
    )
    cluster_result = clusterer.cluster(
        ssa_result=ssa_result,
        trend_component=0,
        max_components=component_count,
    )

    trend_series = decomposer.reconstruct_component(0)
    component_limit = min(component_count, 20, len(ssa_result.Sigma))
    component_series: list[SSALineSeries] = []
    for component_id in range(component_limit):
        component_ts = decomposer.reconstruct_component(component_id)
        component_series.append(
            SSALineSeries(
                label=f"RC{component_id + 1}",
                color=SSA_COLORS[component_id % len(SSA_COLORS)],
                points=ts_points_from_series(component_ts, ts.index),
            )
        )

    grouped_series: list[SSALineSeries] = [
        SSALineSeries(
            label="Исходный ряд",
            color="#2563eb",
            points=ts_points_from_series(ts.values, ts.index),
        ),
        SSALineSeries(
            label="trend",
            color="#7c8798",
            points=ts_points_from_series(trend_series, ts.index),
        ),
    ]

    cluster_series: list[SSALineSeries] = []
    unique_clusters = sorted(cluster_result.reconstructed.keys())
    for idx, cluster_id in enumerate(unique_clusters):
        color = SSA_COLORS[idx % len(SSA_COLORS)]
        reconstructed = cluster_result.reconstructed[cluster_id]
        label = f"Cluster {cluster_id + 1}"
        line = SSALineSeries(
            label=label,
            color=color,
            points=ts_points_from_series(reconstructed, ts.index),
        )
        grouped_series.append(line)
        cluster_series.append(line)

    wcorr_limit = min(component_count, len(ssa_result.wcorr))
    wcorr_matrix = np.asarray(ssa_result.wcorr[:wcorr_limit, :wcorr_limit], dtype=float)

    cumulative_points = [
        SSACumulativePoint(component=int(i + 1), cumulative=float(value))
        for i, value in enumerate(cluster_result.cumulative_contribution[:component_count])
    ]

    scatter_points: list[SSAScatterPoint] = []
    for idx, row in cluster_result.df_anal.iterrows():
        cluster_value = int(row["cluster"])
        scatter_points.append(
            SSAScatterPoint(
                component=int(row["component"]) + 1,
                cluster=cluster_value + 1,
                frequency=float(row["frequency"]),
                amplitude=float(row["amplitude"]),
                color=SSA_COLORS[cluster_value % len(SSA_COLORS)],
            )
        )

    analysis_object = device_ids[0] if len(device_ids) == 1 else " + ".join(device_ids)

    return SSAAnalysisResponse(
        summary=SSASummaryResponse(
            analysis_object=analysis_object,
            start_at=start_at.replace("T", " "),
            end_at=end_at.replace("T", " "),
            aggregation_min=aggregation_min,
            window_points=window_points,
            window_hours=round(window_points * aggregation_min / 60.0, 2),
            component_count=min(component_count, len(ssa_result.Sigma)),
            cluster_count=len(unique_clusters),
            sample_count=len(ts),
            fs=fs,
        ),
        original_series=ts_points_from_series(ts.values, ts.index),
        wcorr=wcorr_matrix.tolist(),
        cumulative_contribution=cumulative_points,
        amplitude_frequency=scatter_points,
        grouped_series=grouped_series,
        component_series=component_series,
        cluster_series=cluster_series,
    )


# =========================
# Overview
# =========================

def get_active_meter_count(conn: sqlite3.Connection, stale_after_sec: int = 15) -> tuple[int, int]:
    latest_ts = get_latest_ts(conn, "raw_data", "timestamp")
    if latest_ts is None:
        return 0, 4

    threshold = latest_ts - stale_after_sec

    rows = conn.execute(
        """
        SELECT device_id, MAX(timestamp) AS max_ts
        FROM raw_data
        WHERE metric = 'active_power_avg'
        GROUP BY device_id
        ORDER BY device_id
        """
    ).fetchall()

    active = 0
    for row in rows:
        if row["max_ts"] is not None and float(row["max_ts"]) >= threshold:
            active += 1

    total = len(rows) if rows else 4
    return active, total


def get_current_total_power_and_sparkline(
    conn: sqlite3.Connection,
    mode: str,
    year: int | None,
    month: int | None,
) -> tuple[float | None, list[SparklinePoint], int | None]:
    """
    Возвращает:
    - текущее суммарное потребление мощности,
    - sparkline для суммарной мощности,
    - reference_ts.

    Логика:
    - historical:
        используем agg_5min и суммируем mean_value по окнам
    - online:
        текущее значение = сумма последних available значений по каждому счётчику
        sparkline = сумма по 5-секундным корзинам на основе raw_data
    """

    # =========================
    # HISTORICAL MODE
    # =========================
    if mode == "historical" and year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)

        rows = conn.execute(
            """
            SELECT window_end AS ts, SUM(mean_value) AS total_kw
            FROM agg_5min
            WHERE metric = 'active_power_avg'
              AND window_end >= ?
              AND window_end < ?
            GROUP BY window_end
            ORDER BY window_end
            """,
            (start_ts, end_ts),
        ).fetchall()

        if not rows:
            return None, [], None

        points = [
            SparklinePoint(ts=int(row["ts"]), value=float(row["total_kw"]))
            for row in rows
        ]
        current_value = points[-1].value
        reference_ts = points[-1].ts
        return current_value, points, reference_ts

    # =========================
    # ONLINE MODE
    # =========================

    # 1. Текущее значение:
    # берём последнее значение active_power_avg по каждому счётчику и суммируем
    latest_rows = conn.execute(
        """
        SELECT r.device_id, r.timestamp, r.value
        FROM raw_data r
        JOIN (
            SELECT device_id, MAX(timestamp) AS max_ts
            FROM raw_data
            WHERE metric = 'active_power_avg'
            GROUP BY device_id
        ) last_per_device
          ON r.device_id = last_per_device.device_id
         AND r.timestamp = last_per_device.max_ts
        WHERE r.metric = 'active_power_avg'
        ORDER BY r.device_id
        """
    ).fetchall()

    if not latest_rows:
        return None, [], None

    current_value = float(sum(float(row["value"]) for row in latest_rows))
    reference_ts = int(max(float(row["timestamp"]) for row in latest_rows))

    # 2. Sparkline:
    # строим по 5-секундным корзинам за последний час
    cutoff_ts = int(time.time()) - 3600

    rows = conn.execute(
        """
        SELECT bucket_ts AS ts, AVG(sum_kw) AS total_kw
        FROM (
            SELECT CAST(timestamp / 5 AS INTEGER) * 5 AS bucket_ts,
                   CAST(timestamp AS INTEGER) AS ts_raw,
                   SUM(value) AS sum_kw
            FROM raw_data
            WHERE metric = 'active_power_avg'
              AND timestamp >= ?
            GROUP BY ts_raw
        )
        GROUP BY bucket_ts
        ORDER BY bucket_ts
        """,
        (cutoff_ts,),
    ).fetchall()

    points = [
        SparklinePoint(ts=int(row["ts"]), value=float(row["total_kw"]))
        for row in rows
    ]

    return current_value, points, reference_ts

def get_current_drpi_and_sparkline(
    conn: sqlite3.Connection,
    source_id: str,
    mode: str,
    year: int | None,
    month: int | None,
) -> tuple[float | None, list[SparklinePoint], int | None]:
    if mode == "historical" and year and month:
        ts_filter, params = build_time_filter(mode, "ts", year, month, None)
        params = [source_id, *params]
        rows = conn.execute(
            f"""
            SELECT ts, DRPI
            FROM drpi_results
            WHERE source_id = ?
            {ts_filter}
            ORDER BY ts
            LIMIT 500
            """,
            tuple(params),
        ).fetchall()
    else:
        ts_filter, params = build_time_filter("online", "ts", None, None, 7 * 24 * 3600)
        params = [source_id, *params]
        rows = conn.execute(
            f"""
            SELECT ts, DRPI
            FROM drpi_results
            WHERE source_id = ?
            {ts_filter}
            ORDER BY ts
            """,
            tuple(params),
        ).fetchall()

    if not rows:
        return None, [], None

    points = [SparklinePoint(ts=int(r["ts"]), value=float(r["DRPI"])) for r in rows]
    return points[-1].value, points, points[-1].ts


def get_overview_summary(
    conn: sqlite3.Connection,
    mode: str,
    year: int | None,
    month: int | None,
) -> OverviewSummaryResponse:
    current_drpi, drpi_sparkline, drpi_ref_ts = get_current_drpi_and_sparkline(
        conn, source_id="TOTAL", mode=mode, year=year, month=month
    )
    total_power, total_power_sparkline, power_ref_ts = get_current_total_power_and_sparkline(
        conn, mode=mode, year=year, month=month
    )
    active_meters, total_meters = get_active_meter_count(conn)

    reference_ts = drpi_ref_ts or power_ref_ts

    return OverviewSummaryResponse(
        current_drpi=current_drpi,
        current_total_power_kw=total_power,
        active_meters=active_meters,
        total_meters=total_meters,
        drpi_sparkline=drpi_sparkline,
        total_power_sparkline=total_power_sparkline,
        reference_ts=reference_ts,
    )


def get_overview_power_meters(
    conn: sqlite3.Connection,
    mode: str,
    year: int | None,
    month: int | None,
) -> OverviewPowerMetersResponse:
    if mode == "historical" and year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)
        rows = conn.execute(
            """
            SELECT window_end AS ts, device_id, mean_value
            FROM agg_5min
            WHERE metric = 'active_power_avg'
              AND window_end >= ?
              AND window_end < ?
            ORDER BY device_id, window_end
            """,
            (start_ts, end_ts),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT CAST(timestamp AS INTEGER) AS ts, device_id, value
            FROM raw_data
            WHERE metric = 'active_power_avg'
              AND timestamp >= ?
            ORDER BY device_id, timestamp
            """,
            (int(time.time()) - 3600,),
        ).fetchall()

    by_meter: dict[str, list[TimeSeriesPoint]] = {}
    for row in rows:
        meter_id = str(row["device_id"])
        value = row["mean_value"] if "mean_value" in row.keys() else row["value"]
        by_meter.setdefault(meter_id, []).append(
            TimeSeriesPoint(ts=int(row["ts"]), value=float(value))
        )

    series = [
        SeriesResponse(source_id=meter_id, points=points)
        for meter_id, points in sorted(by_meter.items())
    ]

    return OverviewPowerMetersResponse(
        mode=mode,
        year=year,
        month=month,
        series=series,
    )


def get_drpi_heatmap(
    conn: sqlite3.Connection,
    source_id: str,
    mode: str,
    year: int | None,
    month: int | None,
) -> OverviewHeatmapResponse:
    if mode == "historical" and year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)
        params = (source_id, start_ts, end_ts)
        rows = conn.execute(
            """
            SELECT ts, DRPI
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
              AND ts < ?
            ORDER BY ts
            """,
            params,
        ).fetchall()
    else:
        params = (source_id, int(time.time()) - 30 * 24 * 3600)
        rows = conn.execute(
            """
            SELECT ts, DRPI
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
            ORDER BY ts
            """,
            params,
        ).fetchall()

    weekday_labels = {
        0: "Пн",
        1: "Вт",
        2: "Ср",
        3: "Чт",
        4: "Пт",
        5: "Сб",
        6: "Вс",
    }

    bucket: dict[tuple[int, int], list[float]] = {}
    for row in rows:
        ts = int(row["ts"])
        value = float(row["DRPI"])
        dt = time.localtime(ts)
        weekday = (dt.tm_wday + 0) % 7
        hour = dt.tm_hour
        bucket.setdefault((weekday, hour), []).append(value)

    cells: list[HeatmapCell] = []
    for weekday in range(7):
        for hour in range(24):
            values = bucket.get((weekday, hour), [])
            avg_value = sum(values) / len(values) if values else None
            cells.append(
                HeatmapCell(
                    weekday=weekday,
                    weekday_label=weekday_labels[weekday],
                    hour=hour,
                    value=avg_value,
                )
            )

    return OverviewHeatmapResponse(
        source_id=source_id,
        mode=mode,
        year=year,
        month=month,
        cells=cells,
    )


# =========================
# DRPI page
# =========================

def get_best_dr_days(
    conn: sqlite3.Connection,
    source_id: str,
    mode: str,
    year: int | None,
    month: int | None,
) -> list[str]:
    if mode == "historical" and year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)
        rows = conn.execute(
            """
            SELECT CAST(strftime('%w', datetime(ts, 'unixepoch')) AS INTEGER) AS weekday_sql,
                   AVG(DRPI) AS avg_drpi
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
              AND ts < ?
            GROUP BY weekday_sql
            ORDER BY avg_drpi DESC
            LIMIT 3
            """,
            (source_id, start_ts, end_ts),
        ).fetchall()
    else:
        latest_ts = get_latest_ts_for_drpi_source(conn, source_id)
        start_ts = (latest_ts - 30 * 24 * 3600) if latest_ts is not None else int(time.time()) - 30 * 24 * 3600
        rows = conn.execute(
            """
            SELECT CAST(strftime('%w', datetime(ts, 'unixepoch')) AS INTEGER) AS weekday_sql,
                   AVG(DRPI) AS avg_drpi
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
            GROUP BY weekday_sql
            ORDER BY avg_drpi DESC
            LIMIT 3
            """,
            (source_id, start_ts),
        ).fetchall()

    labels = {
        1: "Пн",
        2: "Вт",
        3: "Ср",
        4: "Чт",
        5: "Пт",
        6: "Сб",
        0: "Вс",
    }

    return [labels[int(r["weekday_sql"])] for r in rows]


def get_drpi_min_max_24h(conn: sqlite3.Connection, source_id: str) -> tuple[float | None, float | None]:
    latest_ts = get_latest_ts_for_drpi_source(conn, source_id)
    if latest_ts is None:
        return None, None

    row = conn.execute(
        """
        SELECT MIN(DRPI) AS min_drpi, MAX(DRPI) AS max_drpi
        FROM drpi_results
        WHERE source_id = ?
          AND ts >= ?
        """,
        (source_id, latest_ts - 24 * 3600),
    ).fetchone()

    if row is None:
        return None, None

    min_val = float(row["min_drpi"]) if row["min_drpi"] is not None else None
    max_val = float(row["max_drpi"]) if row["max_drpi"] is not None else None
    return min_val, max_val


def get_latest_ts_for_drpi_source(conn: sqlite3.Connection, source_id: str) -> int | None:
    value = query_scalar(
        conn,
        """
        SELECT MAX(ts)
        FROM drpi_results
        WHERE source_id = ?
        """,
        (source_id,),
    )
    return int(value) if value is not None else None


def get_latest_drpi_row(conn: sqlite3.Connection, source_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT ts, DRPI, F1, F2, F3
        FROM drpi_results
        WHERE source_id = ?
        ORDER BY ts DESC
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()


def get_component_sparkline(
    conn: sqlite3.Connection,
    source_id: str,
    component_name: str,
    horizon_sec: int = 7 * 24 * 3600,
) -> list[SparklinePoint]:
    latest_ts = get_latest_ts_for_drpi_source(conn, source_id)
    if latest_ts is None:
        return []

    rows = conn.execute(
        f"""
        SELECT ts, {component_name} AS value
        FROM drpi_results
        WHERE source_id = ?
          AND ts >= ?
        ORDER BY ts
        """,
        (source_id, latest_ts - horizon_sec),
    ).fetchall()

    return [SparklinePoint(ts=int(r["ts"]), value=float(r["value"])) for r in rows]


def get_drpi_summary(
    conn: sqlite3.Connection,
    source_id: str,
    mode: str,
    year: int | None,
    month: int | None,
) -> DRPISummaryResponse:
    latest_row = get_latest_drpi_row(conn, source_id)
    preferred_days = get_best_dr_days(conn, source_id, mode, year, month)
    min_24h, max_24h = get_drpi_min_max_24h(conn, source_id)

    sparkline_f1 = get_component_sparkline(conn, source_id, "F1")
    sparkline_f2 = get_component_sparkline(conn, source_id, "F2")
    sparkline_f3 = get_component_sparkline(conn, source_id, "F3")

    return DRPISummaryResponse(
        source_id=source_id,
        current_drpi=float(latest_row["DRPI"]) if latest_row else None,
        preferred_days=preferred_days,
        min_24h=min_24h,
        max_24h=max_24h,
        current_f1=float(latest_row["F1"]) if latest_row else None,
        current_f2=float(latest_row["F2"]) if latest_row else None,
        current_f3=float(latest_row["F3"]) if latest_row else None,
        sparkline_f1=sparkline_f1,
        sparkline_f2=sparkline_f2,
        sparkline_f3=sparkline_f3,
        reference_ts=int(latest_row["ts"]) if latest_row else None,
    )


def get_drpi_history(
    conn: sqlite3.Connection,
    source_id: str,
    mode: str,
    year: int | None,
    month: int | None,
) -> DRPIHistoryResponse:
    if mode == "historical" and year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)
        rows = conn.execute(
            """
            SELECT ts, DRPI
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
              AND ts < ?
            ORDER BY ts
            """,
            (source_id, start_ts, end_ts),
        ).fetchall()
    else:
        latest_ts = get_latest_ts_for_drpi_source(conn, source_id)
        start_ts = (latest_ts - 7 * 24 * 3600) if latest_ts is not None else int(time.time()) - 7 * 24 * 3600
        rows = conn.execute(
            """
            SELECT ts, DRPI
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
            ORDER BY ts
            """,
            (source_id, start_ts),
        ).fetchall()

    return DRPIHistoryResponse(
        source_id=source_id,
        mode=mode,
        year=year,
        month=month,
        drpi=[TimeSeriesPoint(ts=int(r["ts"]), value=float(r["DRPI"])) for r in rows],
    )


def get_drpi_components(
    conn: sqlite3.Connection,
    source_id: str,
    mode: str,
    year: int | None,
    month: int | None,
) -> DRPIComponentsResponse:
    if mode == "historical" and year and month:
        start_ts, end_ts = to_unix_month_bounds(year, month)
        rows = conn.execute(
            """
            SELECT ts, F1, F2, F3
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
              AND ts < ?
            ORDER BY ts
            """,
            (source_id, start_ts, end_ts),
        ).fetchall()
    else:
        latest_ts = get_latest_ts_for_drpi_source(conn, source_id)
        start_ts = (latest_ts - 7 * 24 * 3600) if latest_ts is not None else int(time.time()) - 7 * 24 * 3600
        rows = conn.execute(
            """
            SELECT ts, F1, F2, F3
            FROM drpi_results
            WHERE source_id = ?
              AND ts >= ?
            ORDER BY ts
            """,
            (source_id, start_ts),
        ).fetchall()

    f1 = [TimeSeriesPoint(ts=int(r["ts"]), value=float(r["F1"])) for r in rows]
    f2 = [TimeSeriesPoint(ts=int(r["ts"]), value=float(r["F2"])) for r in rows]
    f3 = [TimeSeriesPoint(ts=int(r["ts"]), value=float(r["F3"])) for r in rows]

    return DRPIComponentsResponse(
        source_id=source_id,
        mode=mode,
        year=year,
        month=month,
        f1=f1,
        f2=f2,
        f3=f3,
    )
