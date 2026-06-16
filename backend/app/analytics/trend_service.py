from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.analytics.aggregation_service import AGGREGATION_TABLES


def parse_time(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text).timestamp()


def iso_from_ts(value: float) -> str:
    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()


def aggregation_table(aggregation: str) -> str:
    if aggregation == "raw":
        return "measurements_raw"
    if aggregation not in AGGREGATION_TABLES:
        raise ValueError("Unsupported aggregation")
    return AGGREGATION_TABLES[aggregation]


def trend_series(
    conn,
    *,
    device_id: Optional[int],
    metric: str,
    aggregation: str,
    from_value: Optional[str],
    to_value: Optional[str],
    limit: int,
) -> dict[str, Any]:
    from_ts = parse_time(from_value)
    to_ts = parse_time(to_value)
    params: list[Any] = [metric]
    clauses = ["metric = ?"]
    if device_id is not None:
        clauses.append("device_id = ?")
        params.append(device_id)
    if aggregation == "raw":
        ts_col = "timestamp"
        value_col = "value"
        unit_col = "unit"
    else:
        ts_col = "window_end"
        value_col = "mean_value"
        unit_col = "unit"
    if from_ts is not None:
        clauses.append(f"{ts_col} >= ?")
        params.append(from_ts)
    if to_ts is not None:
        clauses.append(f"{ts_col} <= ?")
        params.append(to_ts)
    params.append(limit)
    table_name = aggregation_table(aggregation)
    rows = conn.execute(
        f"""
        SELECT {ts_col} AS ts, {value_col} AS value, {unit_col} AS unit
        FROM {table_name}
        WHERE {' AND '.join(clauses)}
        ORDER BY {ts_col} DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    ordered = list(reversed(rows))
    return {
        "device_id": device_id,
        "metric": metric,
        "unit": ordered[-1]["unit"] if ordered else None,
        "aggregation": aggregation,
        "points": [{"ts": iso_from_ts(row["ts"]), "value": float(row["value"])} for row in ordered],
    }


def trend_summary(conn, *, metric: str, aggregation: str, from_value: Optional[str], to_value: Optional[str]) -> dict[str, Any]:
    from_ts = parse_time(from_value)
    to_ts = parse_time(to_value)
    table_name = aggregation_table(aggregation)
    if aggregation == "raw":
        ts_col = "timestamp"
        value_col = "value"
    else:
        ts_col = "window_end"
        value_col = "mean_value"
    clauses = ["metric = ?"]
    params: list[Any] = [metric]
    if from_ts is not None:
        clauses.append(f"{ts_col} >= ?")
        params.append(from_ts)
    if to_ts is not None:
        clauses.append(f"{ts_col} <= ?")
        params.append(to_ts)
    row = conn.execute(
        f"""
        SELECT AVG({value_col}) AS mean, MIN({value_col}) AS min, MAX({value_col}) AS max, COUNT(*) AS sample_count
        FROM {table_name}
        WHERE {' AND '.join(clauses)}
        """,
        params,
    ).fetchone()
    return {
        "metric": metric,
        "aggregation": aggregation,
        "from": from_value,
        "to": to_value,
        "mean": float(row["mean"]) if row["mean"] is not None else None,
        "min": float(row["min"]) if row["min"] is not None else None,
        "max": float(row["max"]) if row["max"] is not None else None,
        "sample_count": int(row["sample_count"] or 0),
    }


def trend_metrics(conn) -> dict[str, Any]:
    devices = [dict(row) for row in conn.execute("SELECT id, name, enabled FROM devices ORDER BY name").fetchall()]
    metrics = {
        row["metric"]
        for row in conn.execute(
            """
            SELECT metric FROM measurements_raw
            UNION
            SELECT metric FROM measurements_agg_5min
            ORDER BY metric
            """
        ).fetchall()
    }
    return {"devices": devices, "metrics": sorted(metrics)}
