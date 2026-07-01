"""SQLAlchemy async engine and session factory."""

from __future__ import annotations

import contextvars
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, with_loader_criteria

from sentineldb.core.config import settings

# Holds the UUID tenant identifier for the active request or worker task.
tenant_context: contextvars.ContextVar[uuid.UUID | None] = contextvars.ContextVar(
    "tenant_context", default=None
)

# prepared_statement_cache_size=0 required for Supabase PgBouncer pooler
# compatibility — must be passed via connect_args, not as a top-level kwarg.
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"prepared_statement_cache_size": 0},
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """
    Transparently append .where(Model.tenant_id == tenant_id) to all ORM queries
    on models inheriting from TenantMixin.
    """
    tenant_id = tenant_context.get()

    if (
        tenant_id is not None
        and hasattr(execute_state.statement, "options")
        and not execute_state.execution_options.get("skip_tenant_filter", False)
    ):
        # We import TenantMixin here locally to avoid circular imports,
        # since models.py imports tenant_context from session.py
        from sentineldb.db.models import TenantMixin

        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                TenantMixin,
                lambda cls: cls.tenant_id == tenant_id,
                include_aliases=True,
                propagate_to_loaders=True,
            )
        )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

