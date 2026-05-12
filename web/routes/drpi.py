from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from web.db import (
    get_connection,
    get_drpi_components,
    get_drpi_history,
    get_drpi_summary,
    get_meter_options,
    get_year_month_options,
)
from web.schemas import DRPIComponentsResponse, DRPIHistoryResponse, DRPISummaryResponse

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/drpi", response_class=HTMLResponse)
async def drpi_page(request: Request):
    conn = get_connection()
    try:
        meter_options = get_meter_options(conn)
        year_options, month_options = get_year_month_options(conn)
    finally:
        conn.close()

    return templates.TemplateResponse(
        request,
        "drpi.html",
        {
            "title": "Индекс DRPI",
            "page_name": "drpi",
            "meter_options": meter_options,
            "year_options": year_options,
            "month_options": month_options,
            "defaults": {
                "mode": "online",
                "source_id": "TOTAL",
                "year": None,
                "month": None,
            },
        },
    )


@router.get("/api/drpi/summary", response_model=DRPISummaryResponse)
async def drpi_summary_api(
    source_id: str = Query(default="TOTAL"),
    mode: str = Query(default="online"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    conn = get_connection()
    try:
        return get_drpi_summary(conn, source_id=source_id, mode=mode, year=year, month=month)
    finally:
        conn.close()


@router.get("/api/drpi/history", response_model=DRPIHistoryResponse)
async def drpi_history_api(
    source_id: str = Query(default="TOTAL"),
    mode: str = Query(default="online"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    conn = get_connection()
    try:
        return get_drpi_history(conn, source_id=source_id, mode=mode, year=year, month=month)
    finally:
        conn.close()


@router.get("/api/drpi/components", response_model=DRPIComponentsResponse)
async def drpi_components_api(
    source_id: str = Query(default="TOTAL"),
    mode: str = Query(default="online"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    conn = get_connection()
    try:
        return get_drpi_components(conn, source_id=source_id, mode=mode, year=year, month=month)
    finally:
        conn.close()
