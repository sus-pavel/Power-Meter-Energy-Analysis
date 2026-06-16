from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import Database, require_permission
from backend.app.analytics.trend_service import trend_metrics, trend_series, trend_summary
from backend.app.core.config import settings


router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/series")
def get_series(
    conn: Database,
    _: object = Depends(require_permission("view_analytics")),
    device_id: Optional[int] = None,
    metric: str = settings.analytics_metric_name,
    aggregation: str = "5min",
    from_value: Optional[str] = Query(default=None, alias="from"),
    to_value: Optional[str] = Query(default=None, alias="to"),
    limit: int = Query(default=500, ge=1, le=5000),
):
    try:
        return trend_series(conn, device_id=device_id, metric=metric, aggregation=aggregation, from_value=from_value, to_value=to_value, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/summary")
def get_summary(
    conn: Database,
    _: object = Depends(require_permission("view_analytics")),
    metric: str = settings.analytics_metric_name,
    aggregation: str = "5min",
    from_value: Optional[str] = Query(default=None, alias="from"),
    to_value: Optional[str] = Query(default=None, alias="to"),
):
    try:
        return trend_summary(conn, metric=metric, aggregation=aggregation, from_value=from_value, to_value=to_value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/metrics")
def get_metrics(conn: Database, _: object = Depends(require_permission("view_analytics"))):
    return trend_metrics(conn)
