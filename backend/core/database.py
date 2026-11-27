"""
database.py

Resilient Multi-Storage Database Manager for the Digital Twin Platform (P4-A).
Dynamically switches between PostgreSQL + TimescaleDB + PostGIS and
resilient local SQLite + aiosqlite fallback with zero manual configuration.
"""

import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional
from urllib.parse import urlparse

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from .config import settings

logger = logging.getLogger("digital_twin.database")
Base = declarative_base()

_LOCAL_POSTGRES_HOSTS = {"127.0.0.1", "localhost", "::1", "postgres", "timescaledb", "db"}


def is_hosted_pooler_url(url: str) -> bool:
    """
    Determines whether a PostgreSQL connection URL targets a hosted connection pooler
    or managed cloud database (e.g. Supabase Supavisor/PgBouncer, Neon pooler, RDS)
    that drops idle connections aggressively. Returns False for SQLite or local Postgres.
    """
    raw = (url or "").strip()
    if not raw or raw.startswith("sqlite"):
        return False
    parsed = urlparse(raw)
    host = (parsed.hostname or "").strip().lower()
    query = (parsed.query or "").strip().lower()
    port = parsed.port

    if any(marker in host for marker in ("pooler.supabase.com", "supabase.co", "-pooler.", ".pooler.", "pgbouncer")):
        return True
    if "pgbouncer=true" in query or port == 6543:
        return True
    if host and host not in _LOCAL_POSTGRES_HOSTS:
        return True
    return False


def build_postgres_engine_kwargs(async_url: str) -> Dict[str, Any]:
    """
    Constructs SQLAlchemy async engine pool arguments for PostgreSQL targets.
    Hosted poolers receive bounded pool sizes and 300s connection recycling while
    keeping pool_pre_ping enabled.
    """
    parsed = urlparse(async_url)
    host = (parsed.hostname or "").strip().lower()
    query = (parsed.query or "").strip().lower()
    port = parsed.port

    hosted = is_hosted_pooler_url(async_url)
    async_args: Dict[str, Any] = {}
    if any(marker in host for marker in ("supabase.co", "pooler.supabase.com", "neon.tech")):
        async_args["ssl"] = "require"
    if port == 6543 or "pgbouncer" in host or "pgbouncer=true" in query:
        async_args["statement_cache_size"] = 0

    if hosted:
        return {
            "echo": False,
            "pool_size": int(settings.DB_HOSTED_POOL_SIZE),
            "max_overflow": int(settings.DB_HOSTED_MAX_OVERFLOW),
            "pool_recycle": int(settings.DB_POOL_RECYCLE_SEC),
            "pool_pre_ping": True,
            "connect_args": async_args,
        }

    return {
        "echo": False,
        "pool_size": int(settings.DB_POOL_SIZE),
        "max_overflow": int(settings.DB_MAX_OVERFLOW),
        "pool_pre_ping": True,
        "connect_args": async_args,
    }


class PersistenceAdapterManager:
    """
    Manages dynamic database engine instantiation, connection health probing,
    and driver-specific dialect configurations.
    """

    def __init__(self):
        self._active_backend: str = "sqlite"
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialize_engine()

    def _probe_postgres(self) -> bool:
        """Quickly probes if primary PostgreSQL instance is reachable and authenticates."""
        try:
            sync_url = settings.sync_database_url
            connect_args: Dict[str, Any] = {"connect_timeout": int(max(1, settings.DB_CONNECT_TIMEOUT_SEC))}
            if "supabase.co" in sync_url or "pooler.supabase.com" in sync_url:
                connect_args["sslmode"] = "require"
            probe_engine = create_engine(
                sync_url,
                connect_args=connect_args,
                pool_pre_ping=True
            )
            with probe_engine.connect() as conn:
                res = conn.execute(text("SELECT 1"))
                is_ok = res.scalar() == 1
                probe_engine.dispose()
                return is_ok
        except Exception as e:
            logger.warning(
                "Primary PostgreSQL probe failed (%s): %s. Operating with resilient SQLite fallback.",
                type(e).__name__,
                str(e).strip()[:100]
            )
            return False

    def _initialize_engine(self) -> None:
        target_backend = settings.DATABASE_BACKEND.lower().strip()
        use_postgres = False

        if target_backend == "postgres":
            use_postgres = True
        elif target_backend == "sqlite":
            use_postgres = False
        else:  # "auto"
            use_postgres = self._probe_postgres()

        if use_postgres:
            self._active_backend = "postgresql"
            async_url = settings.async_database_url
            pg_kwargs = build_postgres_engine_kwargs(async_url)
            logger.info(
                "Initializing primary PostgreSQL persistence engine (hosted_pooler=%s, pool_size=%s, max_overflow=%s, pool_recycle=%s).",
                is_hosted_pooler_url(async_url),
                pg_kwargs.get("pool_size"),
                pg_kwargs.get("max_overflow"),
                pg_kwargs.get("pool_recycle"),
            )
            self._engine = create_async_engine(async_url, **pg_kwargs)
        else:
            self._active_backend = "sqlite"
            sqlite_path = settings.resolved_sqlite_path
            logger.info("Activating resilient local SQLite persistence engine at %s", sqlite_path)
            self._engine = create_async_engine(
                settings.sqlite_async_url,
                echo=False,
                future=True,
                poolclass=NullPool,
                connect_args={"timeout": 15.0},
            )

            # Register SQLite hooks for WAL mode, foreign keys, and custom SQL functions
            @event.listens_for(self._engine.sync_engine, "connect")
            def _setup_sqlite_connection(dbapi_conn, connection_record):
                try:
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA busy_timeout=15000;")
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA foreign_keys=ON;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                    cursor.close()
                except Exception as ex:
                    logger.debug("SQLite PRAGMA setup notice: %s", ex)

                # Register custom functions for cross-database SQL compatibility (NOW() support)
                if hasattr(dbapi_conn, "create_function"):
                    dbapi_conn.create_function("NOW", 0, lambda: datetime.now(timezone.utc).isoformat())
                elif hasattr(dbapi_conn, "_connection") and hasattr(dbapi_conn._connection, "create_function"):
                    dbapi_conn._connection.create_function("NOW", 0, lambda: datetime.now(timezone.utc).isoformat())

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    def switch_backend(self, backend: str) -> None:
        """Dynamically switches backend between postgresql and sqlite (primarily for testing)."""
        settings.DATABASE_BACKEND = backend
        self._initialize_engine()

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._initialize_engine()
        if self._engine is None:
            raise RuntimeError("Database engine failed to initialize.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._initialize_engine()
        if self._session_factory is None:
            raise RuntimeError("Database session factory failed to initialize.")
        return self._session_factory

    @property
    def active_backend(self) -> str:
        return self._active_backend

    async def check_health(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error("Database health check probe failed: %s", e)
            return False

    def get_info(self) -> Dict[str, Any]:
        return {
            "backend": self._active_backend,
            "isFallback": self._active_backend == "sqlite",
            "databaseName": settings.POSTGRES_DB if self._active_backend == "postgresql" else str(settings.resolved_sqlite_path.name),
            "targetConfigured": settings.DATABASE_BACKEND,
            "status": "ONLINE"
        }


# Global singleton adapter
persistence_manager = PersistenceAdapterManager()
async_engine = persistence_manager.engine
AsyncSessionLocal = persistence_manager.session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with persistence_manager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for FastAPI Depends(get_db)
get_db = get_db_session


async def check_db_health() -> bool:
    return await persistence_manager.check_health()


def get_active_backend() -> str:
    return persistence_manager.active_backend


def get_persistence_info() -> Dict[str, Any]:
    return persistence_manager.get_info()
