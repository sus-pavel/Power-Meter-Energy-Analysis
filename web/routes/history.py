from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from web.db import (
    get_connection,
    get_day_options,
    get_stream_realtime,
    get_stream_series,
    get_year_month_options,
)
from web.schemas import StreamRealtimeResponse, StreamSeriesResponse

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    conn = get_connection()
    try:
        year_options, month_options = get_year_month_options(conn)
        day_options = get_day_options(conn)
    finally:
        conn.close()

    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "title": "Поток данных в режиме реального времени",
            "page_name": "history",
            "year_options": year_options,
            "month_options": month_options,
            "day_options": day_options,
            "aggregation_options": [5, 10, 15, 30, 60],
            "defaults": {
                "mode": "online",
                "aggregation_min": 5,
            },
        },
    )


@router.get("/api/history/realtime", response_model=StreamRealtimeResponse)
async def history_realtime_api():
    conn = get_connection()
    try:
        return get_stream_realtime(conn)
    finally:
        conn.close()


@router.get("/api/history/series", response_model=StreamSeriesResponse)
async def history_series_api(
    mode: str = Query(default="online"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    day: int | None = Query(default=None),
    aggregation_min: int | None = Query(default=5),
):
    conn = get_connection()
    try:
        return get_stream_series(
            conn,
            mode=mode,
            year=year,
            month=month,
            day=day,
            aggregation_min=aggregation_min,
        )
    finally:
        conn.close()
