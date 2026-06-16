from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.analytics.ssa_app_service import analyze_ssa
from backend.app.api.deps import Database, require_permission
from backend.app.core.config import settings


router = APIRouter(prefix="/api/ssa", tags=["ssa"])


class SSAAnalyzeRequest(BaseModel):
    device_ids: list[int] = Field(default_factory=list)
    metric: str = settings.analytics_metric_name
    aggregation: str = "30min"
    from_value: Optional[str] = Field(default=None, alias="from")
    to_value: Optional[str] = Field(default=None, alias="to")
    window_points: int = Field(default=48, ge=2)
    component_count: int = Field(default=20, ge=1, le=100)
    cluster_count: int = Field(default=4, ge=1, le=20)


@router.post("/analyze")
def analyze(payload: SSAAnalyzeRequest, conn: Database, _: object = Depends(require_permission("view_analytics"))):
    try:
        return analyze_ssa(
            conn,
            device_ids=payload.device_ids,
            metric=payload.metric,
            aggregation=payload.aggregation,
            from_value=payload.from_value,
            to_value=payload.to_value,
            window_points=payload.window_points,
            component_count=payload.component_count,
            cluster_count=payload.cluster_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
