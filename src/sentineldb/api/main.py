"""
FastAPI application factory.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sentineldb.api.routes_alerts import router as alerts_router
from sentineldb.api.routes_config import router as config_router
from sentineldb.api.routes_incidents import router as incidents_router
from sentineldb.api.routes_stream import router as stream_router
from sentineldb.api.routes_tenant import router as tenant_router
from sentineldb.core.config import settings

app = FastAPI(
    title="SentinelDB API",
    description="Read-only DB incident analysis assistant.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts_router)
app.include_router(incidents_router)
app.include_router(stream_router)
app.include_router(config_router)
app.include_router(tenant_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
