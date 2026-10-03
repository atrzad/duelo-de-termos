from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import DADOS_DIR, get_settings


class Base(DeclarativeBase):
    pass


def criar_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or get_settings().database_url
    if url.startswith("sqlite"):
        DADOS_DIR.mkdir(parents=True, exist_ok=True)
    return create_async_engine(url)


engine = criar_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
