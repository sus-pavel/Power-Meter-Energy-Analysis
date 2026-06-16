from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.app.analytics.drpi_app_service import drpi_service
from backend.app.analytics.trend_service import iso_from_ts, parse_time
from backend.app.api.deps import Database, require_permission
from backend.app.models.user import User


router = APIRouter(prefix="/api/drpi", tags=["drpi"])


@router.get("/summary")
def drpi_summary(conn: Database, _: object = Depends(require_permission("view_analytics"))):
    latest = conn.execute("SELECT MAX(ts) FROM app_drpi_results").fetchone()[0]
    if latest is None:
        return {"latest_ts": None, "sources": []}
    rows = conn.execute(
        """
        SELECT source_id, F1, F2, F3, R_raw, DRPI
        FROM app_drpi_results
        WHERE ts = ?
        ORDER BY source_id
        """,
        (latest,),
    ).fetchall()
    return {"latest_ts": iso_from_ts(latest), "sources": [dict(row) for row in rows]}


@router.get("/history")
def drpi_history(
    conn: Database,
    _: object = Depends(require_permission("view_analytics")),
    source_id: str = "TOTAL",
    from_value: Optional[str] = Query(default=None, alias="from"),
    to_value: Optional[str] = Query(default=None, alias="to"),
    limit: int = Query(default=500, ge=1, le=5000),
):
    clauses = ["source_id = ?"]
    params = [source_id]
    from_ts = parse_time(from_value)
    to_ts = parse_time(to_value)
    if from_ts is not None:
        clauses.append("ts >= ?")
        params.append(from_ts)
    if to_ts is not None:
        clauses.append("ts <= ?")
        params.append(to_ts)
    params.append(limit)
    rows = conn.execute(
        f"SELECT ts, DRPI FROM app_drpi_results WHERE {' AND '.join(clauses)} ORDER BY ts DESC LIMIT ?",
        params,
    ).fetchall()
    return {"source_id": source_id, "points": [{"ts": iso_from_ts(row["ts"]), "value": row["DRPI"]} for row in reversed(rows)]}


@router.get("/components")
def drpi_components(conn: Database, _: object = Depends(require_permission("view_analytics")), source_id: str = "TOTAL", limit: int = Query(default=500, ge=1, le=5000)):
    rows = conn.execute(
        """
        SELECT ts, F1, F2, F3, DRPI
        FROM app_drpi_results
        WHERE source_id = ?
        ORDER BY ts DESC
        LIMIT ?
        """,
        (source_id, limit),
    ).fetchall()
    return {
        "source_id": source_id,
        "points": [
            {"ts": iso_from_ts(row["ts"]), "F1": row["F1"], "F2": row["F2"], "F3": row["F3"], "DRPI": row["DRPI"]}
            for row in reversed(rows)
        ],
    }


@router.post("/recalculate")
def drpi_recalculate(_: User = Depends(require_permission("manage_analytics"))):
    stats = drpi_service.run_once()
    return {"inserted": stats.inserted, "sources": stats.sources, "recalculated_at": datetime.now(tz=timezone.utc).isoformat()}
