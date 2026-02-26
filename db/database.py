"""
Database — async SQLAlchemy with SQLite (swap URL for Postgres in prod)
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_raw_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trendwriter.db").strip().strip('"').strip("'")

# Normalize Neon/Supabase URLs automatically
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_url.startswith("postgresql://") and "+asyncpg" not in _raw_url:
    _raw_url = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# asyncpg expects `ssl=require` and does not support `channel_binding`.
if _raw_url.startswith("postgresql+asyncpg://"):
    parts = urlsplit(_raw_url)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    if params.get("sslmode") == "require":
        params.pop("sslmode")
        params["ssl"] = "require"
    params.pop("channel_binding", None)
    _raw_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))

DATABASE_URL = _raw_url
_is_sqlite = DATABASE_URL.startswith("sqlite")

_engine_kwargs = {} if _is_sqlite else {"pool_size": 5, "max_overflow": 10}
engine = create_async_engine(DATABASE_URL, echo=False, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create all tables on startup."""
    from models import user, content, analytics  # noqa: F401 — registers models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
