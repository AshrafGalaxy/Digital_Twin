"""
test_database_pool_recycling.py

Hermetic test suite for Issue #57 ([ENH-02]):
1. Hosted PostgreSQL pooler URLs configure pool_recycle (~300s), bounded pool_size/max_overflow,
   and pool_pre_ping=True.
2. Local PostgreSQL URLs preserve local pool sizing and pool_pre_ping=True.
3. SQLite fallback initializes cleanly with zero pool_recycle argument.
4. Zero emojis and zero em/en dashes across modified files.
"""

from pathlib import Path
import re
from unittest.mock import MagicMock, patch

from backend.core.config import settings
from backend.core.database import (
    PersistenceAdapterManager,
    build_postgres_engine_kwargs,
    is_hosted_pooler_url,
)


ROOT_DIR = Path(__file__).resolve().parent.parent


def test_hosted_pooler_url_detection():
    """Distinguishes hosted poolers and cloud PostgreSQL hosts from local Postgres and SQLite."""
    assert is_hosted_pooler_url("postgresql+asyncpg://u:p@aws-0-ap-south-1.pooler.supabase.com:6543/postgres") is True
    assert is_hosted_pooler_url("postgresql+asyncpg://u:p@db.abcdefg.supabase.co:5432/postgres") is True
    assert is_hosted_pooler_url("postgresql+asyncpg://u:p@ep-cool-rain-pooler.us-east-2.aws.neon.tech:5432/neondb") is True
    assert is_hosted_pooler_url("postgresql+asyncpg://u:p@10.20.30.40:5432/prod?pgbouncer=true") is True

    assert is_hosted_pooler_url("postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/digital_twin") is False
    assert is_hosted_pooler_url("postgresql+asyncpg://postgres:postgres@localhost:5432/digital_twin") is False
    assert is_hosted_pooler_url("postgresql+asyncpg://postgres:postgres@postgres:5432/digital_twin") is False
    assert is_hosted_pooler_url("sqlite+aiosqlite:///data/digital_twin.db") is False


def test_hosted_postgres_engine_kwargs_sets_pool_recycle_and_budget():
    """Hosted PostgreSQL URL receives 300s pool_recycle, bounded max_overflow, and pool_pre_ping=True."""
    supabase_pooler_url = "postgresql+asyncpg://postgres.proj:secret@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    kwargs = build_postgres_engine_kwargs(supabase_pooler_url)

    assert kwargs["pool_recycle"] == 300
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_size"] == settings.DB_HOSTED_POOL_SIZE
    assert kwargs["max_overflow"] == settings.DB_HOSTED_MAX_OVERFLOW
    assert (kwargs["pool_size"] + kwargs["max_overflow"]) <= 12
    assert kwargs["connect_args"]["ssl"] == "require"
    assert kwargs["connect_args"]["statement_cache_size"] == 0


def test_local_postgres_engine_kwargs_retains_local_sizing():
    """Local PostgreSQL URL retains local pool sizing with pool_pre_ping enabled."""
    local_url = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/digital_twin"
    kwargs = build_postgres_engine_kwargs(local_url)

    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_size"] == settings.DB_POOL_SIZE
    assert kwargs["max_overflow"] == settings.DB_MAX_OVERFLOW
    assert "pool_recycle" not in kwargs


def test_hosted_postgres_initialization_passes_pool_recycle_to_engine(monkeypatch):
    """Initializing PersistenceAdapterManager with a hosted URL passes pool_recycle and pool_pre_ping."""
    hosted_url = "postgresql://postgres.proj:secret@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    monkeypatch.setattr(settings, "DATABASE_BACKEND", "postgres")
    monkeypatch.setattr(settings, "DATABASE_URL", hosted_url)

    mock_engine = MagicMock()
    mock_engine.sync_engine = MagicMock()

    with patch("backend.core.database.create_async_engine", return_value=mock_engine) as mock_create:
        manager = PersistenceAdapterManager()
        assert manager.active_backend == "postgresql"
        mock_create.assert_called_once()
        _args, call_kwargs = mock_create.call_args
        assert call_kwargs["pool_recycle"] == 300
        assert call_kwargs["pool_pre_ping"] is True
        assert call_kwargs["max_overflow"] == settings.DB_HOSTED_MAX_OVERFLOW
        assert call_kwargs["connect_args"]["ssl"] == "require"


def test_sqlite_fallback_starts_without_pool_recycle(monkeypatch):
    """SQLite fallback engine instantiation must not receive pool_recycle or Postgres pool kwargs."""
    monkeypatch.setattr(settings, "DATABASE_BACKEND", "sqlite")
    monkeypatch.setattr(settings, "DATABASE_URL", None)

    mock_engine = MagicMock()
    mock_engine.sync_engine = MagicMock()

    with patch("backend.core.database.create_async_engine", return_value=mock_engine) as mock_create, \
         patch("backend.core.database.event.listens_for", return_value=lambda fn: fn):
        manager = PersistenceAdapterManager()
        assert manager.active_backend == "sqlite"
        mock_create.assert_called_once()
        _args, call_kwargs = mock_create.call_args
        assert "pool_recycle" not in call_kwargs
        assert "pool_pre_ping" not in call_kwargs
        assert "max_overflow" not in call_kwargs
        assert call_kwargs.get("future") is True


def test_zero_emojis_and_zero_em_dashes_in_database_files():
    """Asserts zero emojis and zero em/en dashes across Issue #57 files."""
    files = [
        ROOT_DIR / "backend" / "core" / "config.py",
        ROOT_DIR / "backend" / "core" / "database.py",
        ROOT_DIR / "tests" / "test_database_pool_recycling.py",
    ]
    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    for fpath in files:
        content = fpath.read_text(encoding="utf-8")
        assert "\u2014" not in content, f"Em dash found in {fpath}"
        assert "\u2013" not in content, f"En dash found in {fpath}"
        assert not emoji_re.search(content), f"Emoji found in {fpath}"
