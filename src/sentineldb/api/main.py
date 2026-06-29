"""
FastAPI application factory.
"""
from __future__ import annotations

from fastapi import FastAPI

from sentineldb.api.routes_alerts import router as alerts_router

app = FastAPI(
    title="SentinelDB API",
    description="Read-only DB incident analysis assistant.",
    version="0.1.0",
)

app.include_router(alerts_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
