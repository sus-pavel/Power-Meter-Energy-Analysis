from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.routes.overview import router as overview_router
from web.routes.drpi import router as drpi_router
from web.routes.history import router as history_router
from web.routes.ssa import router as ssa_router


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Energy Dashboard")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/overview", status_code=302)


app.include_router(overview_router)
app.include_router(drpi_router)
app.include_router(history_router)
app.include_router(ssa_router)
