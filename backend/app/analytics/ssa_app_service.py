from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.app.analytics.trend_service import aggregation_table, iso_from_ts, parse_time
from backend.app.analytics.prototype_compat import prototype_ssa_engine


def _load_series(
    conn,
    *,
    device_ids: list[int],
    metric: str,
    aggregation: str,
    from_value: Optional[str],
    to_value: Optional[str],
) -> pd.Series:
    table_name = aggregation_table(aggregation)
    if aggregation == "raw":
        ts_col = "timestamp"
        value_col = "value"
    else:
        ts_col = "window_end"
        value_col = "mean_value"
    clauses = ["metric = ?"]
    params: list[Any] = [metric]
    if device_ids:
        clauses.append(f"device_id IN ({','.join('?' for _ in device_ids)})")
        params.extend(device_ids)
    from_ts = parse_time(from_value)
    to_ts = parse_time(to_value)
    if from_ts is not None:
        clauses.append(f"{ts_col} >= ?")
        params.append(from_ts)
    if to_ts is not None:
        clauses.append(f"{ts_col} <= ?")
        params.append(to_ts)
    rows = conn.execute(
        f"""
        SELECT {ts_col} AS ts, device_id, {value_col} AS value
        FROM {table_name}
        WHERE {' AND '.join(clauses)}
        ORDER BY {ts_col}, device_id
        """,
        params,
    ).fetchall()
    if not rows:
        return pd.Series(dtype=float)
    df = pd.DataFrame([dict(row) for row in rows])
    pivot = df.pivot_table(index="ts", columns="device_id", values="value", aggfunc="mean").sort_index()
    series = pivot.sum(axis=1, min_count=1).dropna()
    series.index = pd.to_datetime(series.index.astype(float), unit="s")
    return series.astype(float)


def analyze_ssa(
    conn,
    *,
    device_ids: list[int],
    metric: str,
    aggregation: str,
    from_value: Optional[str],
    to_value: Optional[str],
    window_points: int,
    component_count: int,
    cluster_count: int,
) -> dict[str, Any]:
    series = _load_series(
        conn,
        device_ids=device_ids,
        metric=metric,
        aggregation=aggregation,
        from_value=from_value,
        to_value=to_value,
    )
    if len(series) <= window_points:
        raise ValueError(f"SSA requires more than {window_points} points; found {len(series)}.")
    ssa_module = prototype_ssa_engine()
    SSADecomposer = ssa_module.SSADecomposer
    SSAKMeansClusterer = ssa_module.SSAKMeansClusterer
    decomposer = SSADecomposer(series, window_size=window_points)
    ssa_result = decomposer.fit()
    max_components = min(component_count, len(ssa_result.Sigma))
    clusterer = SSAKMeansClusterer(fs=48, n_clusters=cluster_count)
    clustered = clusterer.cluster(ssa_result=ssa_result, trend_component=0, max_components=max_components)
    dates = [iso_from_ts(pd.Timestamp(ts).timestamp()) for ts in series.index]
    trend = decomposer.reconstruct_component(0)
    component_series = []
    for component_id in range(max_components):
        reconstructed = decomposer.reconstruct_component(component_id)
        component_series.append(
            {
                "component": component_id,
                "points": [{"ts": dates[i], "value": float(reconstructed[i])} for i in range(len(dates))],
            }
        )
    cluster_series = []
    for cluster_id, values in clustered.reconstructed.items():
        cluster_series.append(
            {
                "cluster": int(cluster_id),
                "points": [{"ts": dates[i], "value": float(values[i])} for i in range(len(dates))],
            }
        )
    return {
        "original_series": [{"ts": dates[i], "value": float(series.iloc[i])} for i in range(len(dates))],
        "trend_series": [{"ts": dates[i], "value": float(trend[i])} for i in range(len(dates))],
        "component_series": component_series,
        "cluster_series": cluster_series,
        "wcorr_matrix": np.round(ssa_result.wcorr[:max_components, :max_components], 4).tolist(),
        "cumulative_contribution": [
            {"component": int(i), "value": float(value)}
            for i, value in enumerate(ssa_result.cumulative_contribution[:max_components])
        ],
        "amplitude_frequency_points": [
            {
                "component": int(row["component"]),
                "cluster": int(row["cluster"]),
                "frequency": float(row["frequency"]),
                "amplitude": float(row["amplitude"]),
            }
            for _, row in clustered.df_anal.iterrows()
        ],
        "summary": {
            "points": len(series),
            "window_points": window_points,
            "component_count": max_components,
            "cluster_count": len(clustered.reconstructed),
            "metric": metric,
            "aggregation": aggregation,
        },
    }
