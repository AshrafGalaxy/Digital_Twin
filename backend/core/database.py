"""
database.py

Resilient Multi-Storage Database Manager for the Digital Twin Platform (P4-A).
Dynamically switches between PostgreSQL + TimescaleDB + PostGIS and
resilient local SQLite + aiosqlite fallback with zero manual configuration.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from sqlalchemy import create_engine, event, text
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
            probe_engine = create_engine(
                settings.sync_database_url,
                connect_args={"connect_timeout": int(max(1, settings.DB_CONNECT_TIMEOUT_SEC))},
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
            logger.info(
                "Initializing primary PostgreSQL + TimescaleDB engine at %s:%s/%s",
                settings.POSTGRES_HOST,
                settings.POSTGRES_PORT,
                settings.POSTGRES_DB
            )
            self._engine = create_async_engine(
                settings.async_database_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        else:
            self._active_backend = "sqlite"
            sqlite_path = settings.resolved_sqlite_path
            logger.info("Activating resilient local SQLite persistence engine at %s", sqlite_path)
            self._engine = create_async_engine(
                settings.sqlite_async_url,
                echo=False,
                future=True
            )

            # Register SQLite hooks for WAL mode, foreign keys, and custom SQL functions
            @event.listens_for(self._engine.sync_engine, "connect")
            def _setup_sqlite_connection(dbapi_conn, connection_record):
                try:
                    cursor = dbapi_conn.cursor()
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
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._initialize_engine()
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
    async with persistence_manager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    return await persistence_manager.check_health()


def get_active_backend() -> str:
    return persistence_manager.active_backend


def get_persistence_info() -> Dict[str, Any]:
    return persistence_manager.get_info()
