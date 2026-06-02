"""
pytest fixtures for ReceptivIQ-Platform backend tests.
Uses the existing PostgreSQL schema (platform migrations already applied).
Data is cleaned between tests via TRUNCATE.
"""
from __future__ import annotations
import os
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Override DATABASE_URL before importing app modules
_TEST_DB = "postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq"
os.environ["DATABASE_URL"] = _TEST_DB
os.environ["SYNC_DATABASE_URL"] = "postgresql+psycopg2://receptiviq:receptiviq@localhost:5432/receptiviq"
os.environ["TESTING"] = "true"
# Use a fixed valid Fernet test key (32 url-safe base64-encoded bytes)
os.environ.setdefault("ENCRYPTION_KEY", "QH9gMOQPn_ZNMuW0mzDvKjdIDjsNFTAVRaCzgjBg-Zk=")

# Import app modules AFTER env vars are set
from app.core import database as _db_module  # noqa: E402

# Patch app engine to use NullPool (prevents "event loop closed" errors across tests)
_db_module.engine = create_async_engine(_TEST_DB, echo=False, poolclass=NullPool)
_db_module.async_session = async_sessionmaker(
    _db_module.engine, class_=AsyncSession, expire_on_commit=False
)

from app.core.security import get_password_hash, create_access_token  # noqa: E402
from app.main import app  # noqa: E402

# ── Test DB ────────────────────────────────────────────────────────────────────
TEST_DATABASE_URL = "postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq"
# NullPool: no connection reuse — avoids "another operation in progress" between fixtures
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Tables to truncate in safe dependency order (children first)
_TRUNCATE_TABLES = [
    "token_usage",
    "notifications",
    "report_history",
    "report_schedules",
    "audience_exports",
    "attribution_reports",
    "generation_results", "generations",
    "personas",
    "field_mapping_versions", "field_mappings",
    "sync_logs", "integrations", "credentials",
    "consent_records", "dsar_requests", "audit_logs",
    "users", "clients", "agencies",
]


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Truncate all test data between tests."""
    yield
    async with test_engine.begin() as conn:
        tables = ", ".join(_TRUNCATE_TABLES)
        await conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def client():
    """AsyncClient — each request gets its own DB session from get_db."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Seed data helpers ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_agency():
    """Create and commit a test agency."""
    from app.models.agency import Agency, AgencyStatus, AgencyPlan
    agency = Agency(
        id=uuid.uuid4(),
        name="Test Agency",
        slug=f"test-agency-{uuid.uuid4().hex[:8]}",
        status=AgencyStatus.active,
        plan=AgencyPlan.starter,
    )
    async with TestSession() as session:
        session.add(agency)
        await session.commit()
        await session.refresh(agency)
    return agency


@pytest_asyncio.fixture
async def test_user(test_agency):
    """Create and commit an agency_admin test user."""
    from app.models.user import User, UserRole
    from app.core.pii_crypto import encrypt_pii, hash_email
    raw_email = f"admin-{uuid.uuid4().hex[:8]}@test.com"
    raw_name = "Test Admin"
    user = User(
        id=uuid.uuid4(),
        agency_id=test_agency.id,
        email=encrypt_pii(raw_email),
        email_hash=hash_email(raw_email),
        hashed_password=get_password_hash("TestPass123!"),
        full_name=encrypt_pii(raw_name),
        role=UserRole.agency_admin,
        is_active=True,
    )
    async with TestSession() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    # Attach plaintext values for test assertions
    user._raw_email = raw_email
    user._raw_full_name = raw_name
    return user


@pytest_asyncio.fixture
def admin_token(test_user, test_agency):
    """JWT token for test_user."""
    return create_access_token({
        "sub": str(test_user.id),
        "agency_id": str(test_agency.id),
        "role": "agency_admin",
    })


@pytest_asyncio.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
