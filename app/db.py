import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from models import Base  

# Connection string for the async DB engine
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/tokka_intern_assignment",
)

# Global async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,   # set to True to see all SQL in logs
    future=True,
)

# Session factory for getting AsyncSession objects
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session (AsyncSession)
    to request handlers.

    Usage in endpoints:
        async def some_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session


async def run_migrations() -> None:
    """
    Simple, idempotent migration function.

    It will be called on application startup to ensure the required
    tables / columns exist.

    For Stage 3:
    - Create the 'pokemon' table if it does not exist yet.
    """
    async with engine.begin() as conn:
        # We could also use ORM's Base.metadata.create_all, but here we
        # show an explicit SQL-based approach for clarity.
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pokemon (
                    pokemon_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_experience INTEGER,
                    height INTEGER,
                    "order" INTEGER,
                    weight INTEGER,
                    location_area_encounters TEXT
                );
                """
            )
        )

    
