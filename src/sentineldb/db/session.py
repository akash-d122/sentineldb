"""SQLAlchemy async engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sentineldb.core.config import settings

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

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
