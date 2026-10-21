"""
keepalive_service.py

Anti-dormancy keep-alive service for remote cloud database persistence (Supabase Free Tier).
Supabase free instances pause after 7 consecutive days of inactivity. This background worker
dispatches periodic lightweight health queries (SELECT 1) to keep the project active.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import text

from backend.core.database import persistence_manager, get_active_backend
from backend.core.config import settings

logger = logging.getLogger("digital_twin.keepalive")


class KeepAliveService:
    """
    Periodic keep-alive heartbeat manager designed to prevent cloud-hosted
    database instances from entering dormant pause states.
    """

    def __init__(self, interval_hours: float = 24.0):
        self._interval_seconds = interval_hours * 3600.0
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._last_ping_at: Optional[datetime] = None
        self._successful_pings: int = 0
        self._failed_pings: int = 0

    async def ping_database(self) -> bool:
        """
        Executes a minimal non-intrusive query to verify and refresh connection activity.
        """
        try:
            async with persistence_manager.session_factory() as session:
                res = await session.execute(text("SELECT 1 AS keepalive"))
                row = res.scalar()
                if row == 1:
                    self._last_ping_at = datetime.now(timezone.utc)
                    self._successful_pings += 1
                    logger.debug(
                        "Database keep-alive ping succeeded at %s (Total: %s)",
                        self._last_ping_at.isoformat(),
                        self._successful_pings
                    )
                    return True
                return False
        except Exception as e:
            self._failed_pings += 1
            logger.warning(
                "Database keep-alive ping failed (%s): %s",
                type(e).__name__,
                str(e)[:120]
            )
            return False

    async def _heartbeat_loop(self) -> None:
        """Background loop executing pings at configured intervals."""
        while self._running:
            backend = get_active_backend()
            # Only execute keep-alive pings if connected to PostgreSQL / Supabase
            if backend == "postgresql":
                await self.ping_database()
            try:
                await asyncio.sleep(self._interval_seconds)
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        """Starts the background keep-alive task if not already running."""
        if self._running:
            return
        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._heartbeat_loop())
            logger.info(
                "Keep-alive anti-dormancy service started (Interval: %.1fh).",
                self._interval_seconds / 3600.0
            )
        except RuntimeError:
            logger.debug("No running event loop found for keep-alive task initialization.")

    async def stop(self) -> None:
        """Stops the background keep-alive task gracefully."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Keep-alive anti-dormancy service stopped.")

    def get_status(self) -> dict:
        """Returns the operational metrics of the keep-alive manager."""
        return {
            "running": self._running,
            "intervalHours": self._interval_seconds / 3600.0,
            "lastPingAt": self._last_ping_at.isoformat() if self._last_ping_at else None,
            "successfulPings": self._successful_pings,
            "failedPings": self._failed_pings,
            "activeBackend": get_active_backend()
        }


# Global singleton instance
keepalive_service = KeepAliveService(interval_hours=24.0)
