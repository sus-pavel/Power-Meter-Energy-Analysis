from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from web.db import analyze_ssa, get_connection, get_raw_meter_options, get_ssa_page_defaults
from web.schemas import SSAAnalysisResponse

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/ssa", response_class=HTMLResponse)
async def ssa_page(request: Request):
    conn = get_connection()
    try:
        meter_options = get_raw_meter_options(conn)
        defaults = get_ssa_page_defaults(conn, aggregation_min=30)
    finally:
        conn.close()

    return templates.TemplateResponse(
        request,
        "ssa.html",
        {
            "title": "SSA анализ временного ряда",
            "page_name": "ssa",
            "meter_options": meter_options,
            "defaults": defaults,
            "aggregation_options": [5, 10, 15, 30, 60],
        },
    )


@router.get("/api/ssa/analyze", response_model=SSAAnalysisResponse)
async def ssa_analyze_api(
    device_ids: list[str] = Query(...),
    start_at: str = Query(...),
    end_at: str = Query(...),
    aggregation_min: int = Query(default=30),
    window_points: int = Query(default=48),
    component_count: int = Query(default=20),
    cluster_count: int = Query(default=4),
):
    conn = get_connection()
    try:
        return analyze_ssa(
            conn=conn,
            device_ids=device_ids,
            start_at=start_at,
            end_at=end_at,
            aggregation_min=aggregation_min,
            window_points=window_points,
            component_count=component_count,
            cluster_count=cluster_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        conn.close()
