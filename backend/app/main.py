from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.analytics.manager import analytics_manager
from backend.app.api import auth, candidates, dashboard, devices, discovery, drpi, health, operations, polling, ssa, trends, users
from backend.app.core.config import settings
from backend.app.core.database import init_db


app = FastAPI(
    title="PowerMeter App Backend",
    version="0.2.0",
    description="Local-first application backend for PowerMeter.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(tauri|http|https)://(localhost|tauri\.localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    analytics_manager.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await analytics_manager.stop()


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"app": settings.app_name, "mode": settings.app_mode, "docs": "/docs"}


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(discovery.router)
app.include_router(candidates.router)
app.include_router(operations.router)
app.include_router(polling.router)
app.include_router(trends.router)
app.include_router(drpi.router)
app.include_router(ssa.router)
app.include_router(dashboard.router)
