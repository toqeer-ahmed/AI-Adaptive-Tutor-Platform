from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from backend.config import settings

# Polyfill PostgreSQL JSONB type to JSON for SQLite compatibility
@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

is_sqlite = "sqlite" in settings.DATABASE_URL
engine_kwargs = {"echo": settings.DEBUG, "future": True}
if not is_sqlite:
    engine_kwargs.update({"pool_pre_ping": True, "pool_size": 20, "max_overflow": 10})
else:
    engine_kwargs.update({"connect_args": {"check_same_thread": False}})

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """
    Executes SET LOCAL app.current_tenant_id = 'tenant_id' on the session.
    This ensures PostgreSQL RLS policies restrict all subsequent queries on this session.
    """
    if tenant_id and "sqlite" not in settings.DATABASE_URL:
        await session.execute(
            text("SET LOCAL app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )
