from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from sentineldb.api.dependencies import set_tenant_context, verify_jwt
from sentineldb.core.config import settings
from sentineldb.db.models import IncidentORM
from sentineldb.db.session import get_session, tenant_context

router = APIRouter(
    prefix="/api/v1/incidents/stream",
    tags=["stream"],
    dependencies=[Depends(verify_jwt), Depends(set_tenant_context)],
)

logger = logging.getLogger(__name__)


async def event_generator(tenant_id: str, session: AsyncSession) -> AsyncGenerator[str, None]:
    """Generates SSE events for the given tenant."""
    # R4: Fetch latest incident state upon SSE connection
    stmt = select(IncidentORM).order_by(desc(IncidentORM.created_at)).limit(50)
    result = await session.execute(stmt)
    recent_incidents = result.scalars().all()

    initial_states = [
        {"incident_id": str(inc.incident_id), "status": inc.status, "tenant_id": tenant_id}
        for inc in recent_incidents
    ]

    yield f"data: {json.dumps({'type': 'initial_state', 'incidents': initial_states})}\n\n"

    r = redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    channel_name = f"incident_updates:{tenant_id}"

    try:
        await pubsub.subscribe(channel_name)
        logger.info(f"Tenant {tenant_id} subscribed to SSE channel {channel_name}")

        while True:
            # We use get_message with a timeout to allow checking for client disconnects
            # StreamingResponse will raise an exception if client disconnects when we yield
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                # Ensure we yield correctly formatted SSE data
                yield f"data: {data}\n\n"
            else:
                # Keep-alive ping to detect disconnected clients
                yield ": ping\n\n"

    except asyncio.CancelledError:
        logger.info(f"Client disconnected from SSE stream for tenant {tenant_id}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
        await r.aclose()


@router.get("")
async def stream_incidents(session: AsyncSession = Depends(get_session)):
    """SSE endpoint for real-time incident status updates."""
    tenant_id = tenant_context.get()
    if not tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Missing tenant context")

    return StreamingResponse(
        event_generator(str(tenant_id), session), media_type="text/event-stream"
    )
