import pytest
import asyncio
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from httpx import AsyncClient, ASGITransport
from backend.models import Base, Role
from backend.api.main import app
from backend.api.deps import get_db


# Polyfill PostgreSQL JSONB type to JSON for SQLite test engine compatibility
@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
AsyncSessionTest = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionTest() as session:
        # Seed default roles with explicit UUIDs for SQLite compatibility
        roles = [
            Role(id=uuid.uuid4(), name="SuperAdmin", description="Super Admin"),
            Role(id=uuid.uuid4(), name="OrgAdmin", description="Org Admin"),
            Role(id=uuid.uuid4(), name="SchoolAdmin", description="School Admin"),
            Role(id=uuid.uuid4(), name="Teacher", description="Teacher"),
            Role(id=uuid.uuid4(), name="Student", description="Student"),
            Role(id=uuid.uuid4(), name="Parent", description="Parent"),
            Role(id=uuid.uuid4(), name="CurriculumManager", description="Curriculum Manager"),
        ]
        session.add_all(roles)
        await session.commit()
        yield session


    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
