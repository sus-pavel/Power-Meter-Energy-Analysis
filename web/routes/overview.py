from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from web.db import (
    get_connection,
    get_drpi_heatmap,
    get_meter_options,
    get_overview_power_meters,
    get_overview_summary,
    get_year_month_options,
)
from web.schemas import OverviewHeatmapResponse, OverviewPowerMetersResponse, OverviewSummaryResponse

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/overview", response_class=HTMLResponse)
async def overview_page(request: Request):
    conn = get_connection()
    try:
        meter_options = get_meter_options(conn)
        year_options, month_options = get_year_month_options(conn)
    finally:
        conn.close()

    return templates.TemplateResponse(
        request,
        "overview.html",
        {
            "title": "Обзор энергосистемы",
            "page_name": "overview",
            "meter_options": meter_options,
            "year_options": year_options,
            "month_options": month_options,
            "defaults": {
                "mode": "online",
                "year": None,
                "month": None,
            },
        },
    )


@router.get("/api/overview/summary", response_model=OverviewSummaryResponse)
async def overview_summary_api(
    mode: str = Query(default="online"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    conn = get_connection()
    try:
        return get_overview_summary(conn, mode=mode, year=year, month=month)
    finally:
        conn.close()


@router.get("/api/overview/power-meters", response_model=OverviewPowerMetersResponse)
async def overview_power_meters_api(
    mode: str = Query(default="online"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    conn = get_connection()
    try:
        return get_overview_power_meters(conn, mode=mode, year=year, month=month)
    finally:
        conn.close()


@router.get("/api/overview/drpi-heatmap", response_model=OverviewHeatmapResponse)
async def overview_drpi_heatmap_api(
    source_id: str = Query(default="TOTAL"),
    mode: str = Query(default="online"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    conn = get_connection()
    try:
        return get_drpi_heatmap(conn, source_id=source_id, mode=mode, year=year, month=month)
    finally:
        conn.close()
