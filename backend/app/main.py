from __future__ import annotations

from fastapi import FastAPI

from backend.app.api import auth, candidates, dashboard, devices, discovery, health, operations, users
from backend.app.core.config import settings
from backend.app.core.database import init_db


app = FastAPI(
    title="PowerMeter App Backend",
    version="0.3.3-operational-dashboard",
    description="Local-first application backend for PowerMeter.",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


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
app.include_router(dashboard.router)
