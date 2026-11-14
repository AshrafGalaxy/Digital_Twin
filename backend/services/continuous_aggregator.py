"""
continuous_aggregator.py

Native 15-minute Continuous Aggregates Engine for the Digital Twin Platform (P4-B).
Replicates TimescaleDB continuous aggregates across both SQLite and PostgreSQL,
providing performant, time-bucketed rollups for speed, flow, occupancy, and queue metrics.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_active_backend, persistence_manager

logger = logging.getLogger("digital_twin.aggregator")

SQLITE_AGG_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS traffic_15m_aggregates (
    bucket_15m TIMESTAMP NOT NULL,
    segment_id TEXT NOT NULL,
    source_mode TEXT NOT NULL DEFAULT 'REPLAY',
    sample_count INTEGER NOT NULL DEFAULT 1,
    avg_speed_kmh REAL NOT NULL,
    p85_speed_kmh REAL,
    total_flow_veh REAL NOT NULL,
    avg_occupancy_percent REAL NOT NULL,
    avg_queue_length_meters REAL NOT NULL,
    max_queue_length_meters REAL NOT NULL,
    avg_congestion_index REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bucket_15m, segment_id, source_mode)
);
"""

SQLITE_AGG_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_traffic_15m_seg_time ON traffic_15m_aggregates (segment_id, bucket_15m DESC, source_mode);
"""


class ContinuousAggregatorService:
    """
    Computes, materializes, and queries 15-minute rolling continuous aggregates.
    Operates seamlessly across PostgreSQL (TimescaleDB) and SQLite fallback.
    """

    @staticmethod
    async def init_table(session: AsyncSession) -> None:
        """Ensures the continuous aggregates table and index exist."""
        await session.execute(text(SQLITE_AGG_TABLE_DDL))
        await session.execute(text(SQLITE_AGG_INDEX_DDL))
        try:
            check = await session.execute(text("PRAGMA table_info(traffic_15m_aggregates)"))
            cols = [r[1] for r in check.fetchall()]
            if cols and "source_mode" not in cols:
                await session.execute(text("ALTER TABLE traffic_15m_aggregates ADD COLUMN source_mode TEXT NOT NULL DEFAULT 'REPLAY'"))
        except Exception:
            pass
        await session.commit()

    @staticmethod
    async def compute_and_materialize_rollups(session: AsyncSession, hours_back: int = 24) -> int:
        """
        Calculates 15-minute windowed rollups from raw traffic_observations
        and materializes them into traffic_15m_aggregates.
        """
        backend = get_active_backend()
        is_pg = backend == "postgresql"

        start_time = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()

        if is_pg:
            query = text("""
                INSERT INTO traffic_15m_aggregates (
                    bucket_15m, segment_id, source_mode, sample_count, avg_speed_kmh,
                    p85_speed_kmh, total_flow_veh, avg_occupancy_percent,
                    avg_queue_length_meters, max_queue_length_meters, avg_congestion_index
                )
                SELECT
                    time_bucket('15 minutes', observed_at) AS bucket_15m,
                    segment_id,
                    COALESCE(source_mode, 'REPLAY') AS source_mode,
                    COUNT(*) AS sample_count,
                    ROUND(AVG(average_speed_kmh)::numeric, 2) AS avg_speed_kmh,
                    ROUND(PERCENTILE_CONT(0.85) WITHIN GROUP (ORDER BY average_speed_kmh)::numeric, 2) AS p85_speed_kmh,
                    ROUND((AVG(vehicle_flow_per_hour) * 0.25)::numeric, 1) AS total_flow_veh,
                    ROUND(AVG(occupancy_percent)::numeric, 1) AS avg_occupancy_percent,
                    ROUND(AVG(queue_length_meters)::numeric, 1) AS avg_queue_length_meters,
                    ROUND(MAX(queue_length_meters)::numeric, 1) AS max_queue_length_meters,
                    ROUND(AVG(congestion_index)::numeric, 3) AS avg_congestion_index
                FROM traffic_observations
                WHERE observed_at >= :start_time
                GROUP BY 1, 2, 3
                ON CONFLICT (bucket_15m, segment_id, source_mode) DO UPDATE SET
                    sample_count = EXCLUDED.sample_count,
                    avg_speed_kmh = EXCLUDED.avg_speed_kmh,
                    p85_speed_kmh = EXCLUDED.p85_speed_kmh,
                    total_flow_veh = EXCLUDED.total_flow_veh,
                    avg_occupancy_percent = EXCLUDED.avg_occupancy_percent,
                    avg_queue_length_meters = EXCLUDED.avg_queue_length_meters,
                    max_queue_length_meters = EXCLUDED.max_queue_length_meters,
                    avg_congestion_index = EXCLUDED.avg_congestion_index;
            """)
            res = await session.execute(query, {"start_time": start_time})
            await session.commit()
            rowcount = getattr(res, "rowcount", None)
            return int(rowcount) if rowcount is not None else 0
        else:
            # Universal SQLite 15-minute epoch bucketing: ((epoch / 900) * 900)
            obs_query = text("""
                SELECT
                    datetime((strftime('%s', observed_at) / 900) * 900, 'unixepoch') AS bucket_15m,
                    segment_id,
                    COALESCE(source_mode, 'REPLAY') AS source_mode,
                    average_speed_kmh,
                    vehicle_flow_per_hour,
                    occupancy_percent,
                    queue_length_meters,
                    congestion_index
                FROM traffic_observations
                WHERE observed_at >= :start_time
                ORDER BY bucket_15m, segment_id, source_mode, average_speed_kmh
            """)
            obs_res = await session.execute(obs_query, {"start_time": start_time})
            rows = obs_res.mappings().all()
            if not rows:
                return 0

            from collections import defaultdict
            import math

            groups: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
            for r in rows:
                key = (r["bucket_15m"], r["segment_id"], r["source_mode"])
                groups[key].append(r)

            insert_stmt = text("""
                INSERT OR REPLACE INTO traffic_15m_aggregates (
                    bucket_15m, segment_id, source_mode, sample_count, avg_speed_kmh,
                    p85_speed_kmh, total_flow_veh, avg_occupancy_percent,
                    avg_queue_length_meters, max_queue_length_meters, avg_congestion_index
                ) VALUES (
                    :bucket_15m, :segment_id, :source_mode, :sample_count, :avg_speed_kmh,
                    :p85_speed_kmh, :total_flow_veh, :avg_occupancy_percent,
                    :avg_queue_length_meters, :max_queue_length_meters, :avg_congestion_index
                )
            """)

            affected_rows = 0
            for (bucket_15m, segment_id, source_mode), items in groups.items():
                speeds = [float(item["average_speed_kmh"]) for item in items if item["average_speed_kmh"] is not None]
                flows = [float(item["vehicle_flow_per_hour"]) for item in items if item["vehicle_flow_per_hour"] is not None]
                occs = [float(item["occupancy_percent"]) for item in items if item["occupancy_percent"] is not None]
                queues = [float(item["queue_length_meters"]) for item in items if item["queue_length_meters"] is not None]
                congs = [float(item["congestion_index"]) for item in items if item["congestion_index"] is not None]

                sample_count = len(items)
                avg_speed = round(sum(speeds) / len(speeds), 2) if speeds else 0.0

                if speeds:
                    sorted_speeds = sorted(speeds)
                    n = len(sorted_speeds)
                    if n == 1:
                        p85_val = sorted_speeds[0]
                    else:
                        k = (n - 1) * 0.85
                        f = math.floor(k)
                        c = math.ceil(k)
                        if f == c:
                            p85_val = sorted_speeds[int(k)]
                        else:
                            p85_val = sorted_speeds[f] * (c - k) + sorted_speeds[c] * (k - f)
                    p85_speed = round(p85_val, 2)
                else:
                    p85_speed = None

                # Flow rate q (veh/h) converted to 15-minute volume N = q * 0.25
                total_flow = round((sum(flows) / len(flows)) * 0.25, 1) if flows else 0.0
                avg_occ = round(sum(occs) / len(occs), 1) if occs else 0.0
                avg_queue = round(sum(queues) / len(queues), 1) if queues else 0.0
                max_queue = round(max(queues), 1) if queues else 0.0
                avg_cong = round(sum(congs) / len(congs), 3) if congs else 0.0

                await session.execute(insert_stmt, {
                    "bucket_15m": bucket_15m,
                    "segment_id": segment_id,
                    "source_mode": source_mode,
                    "sample_count": sample_count,
                    "avg_speed_kmh": avg_speed,
                    "p85_speed_kmh": p85_speed,
                    "total_flow_veh": total_flow,
                    "avg_occupancy_percent": avg_occ,
                    "avg_queue_length_meters": avg_queue,
                    "max_queue_length_meters": max_queue,
                    "avg_congestion_index": avg_cong,
                })
                affected_rows += 1

            await session.commit()
            return affected_rows

    @staticmethod
    async def get_traffic_rollups(
        session: AsyncSession,
        segment_id: Optional[str] = None,
        source_mode: Optional[str] = None,
        hours_ago: int = 12,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Queries materialized 15-minute rolling aggregates with optional segment and source_mode filtering.
        """
        start_dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        start_time_iso = start_dt.isoformat()
        start_time_std = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        query_str = """
            SELECT bucket_15m, segment_id, source_mode, sample_count, avg_speed_kmh,
                   p85_speed_kmh, total_flow_veh, avg_occupancy_percent,
                   avg_queue_length_meters, max_queue_length_meters, avg_congestion_index
            FROM traffic_15m_aggregates
            WHERE (bucket_15m >= :start_time_iso OR bucket_15m >= :start_time_std)
        """
        params: Dict[str, Any] = {"start_time_iso": start_time_iso, "start_time_std": start_time_std, "limit": limit}

        if segment_id:
            query_str += " AND segment_id = :segment_id"
            params["segment_id"] = segment_id

        if source_mode:
            query_str += " AND source_mode = :source_mode"
            params["source_mode"] = source_mode

        query_str += " ORDER BY bucket_15m DESC, segment_id ASC LIMIT :limit"

        res = await session.execute(text(query_str), params)
        rows = res.mappings().all()

        results = []
        for r in rows:
            bucket_val = r["bucket_15m"]
            bucket_str = bucket_val.isoformat() if isinstance(bucket_val, datetime) else str(bucket_val)
            results.append({
                "bucket15m": bucket_str,
                "segmentId": r["segment_id"],
                "sourceMode": r.get("source_mode", "REPLAY"),
                "sampleCount": r["sample_count"],
                "avgSpeedKmh": float(r["avg_speed_kmh"]),
                "p85SpeedKmh": float(r["p85_speed_kmh"]) if r["p85_speed_kmh"] is not None else float(r["avg_speed_kmh"]),
                "totalFlowVeh": float(r["total_flow_veh"]),
                "avgOccupancyPercent": float(r["avg_occupancy_percent"]),
                "avgQueueLengthMeters": float(r["avg_queue_length_meters"]),
                "maxQueueLengthMeters": float(r["max_queue_length_meters"]),
                "avgCongestionIndex": float(r["avg_congestion_index"])
            })

        return results

    @staticmethod
    async def seed_synthetic_historical_rollups(session: AsyncSession) -> int:
        """
        Seeds synthetic 6-hour historical 15m aggregates if the table has no recent data,
        ensuring immediate visualization data in Traffic Analytics charts.
        Seeded records are explicitly tagged with source_mode = 'SIMULATION'.
        """
        from backend.core.database import get_active_backend
        is_pg = get_active_backend() == "postgresql"

        start_24h_dt = datetime.now(timezone.utc) - timedelta(hours=24)
        if is_pg:
            check = await session.execute(
                text("SELECT COUNT(*) FROM traffic_15m_aggregates WHERE bucket_15m >= :start_dt"),
                {"start_dt": start_24h_dt}
            )
        else:
            check = await session.execute(
                text("SELECT COUNT(*) FROM traffic_15m_aggregates WHERE bucket_15m >= :start_dt"),
                {"start_dt": start_24h_dt.isoformat()}
            )
        if (check.scalar() or 0) > 0:
            return 0

        segments = [
            "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-02",
            "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-01",
            "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-02"
        ]

        now_utc = datetime.now(timezone.utc)
        count = 0

        if is_pg:
            insert_stmt = text("""
                INSERT INTO traffic_15m_aggregates (
                    bucket_15m, segment_id, source_mode, sample_count, avg_speed_kmh,
                    p85_speed_kmh, total_flow_veh, avg_occupancy_percent,
                    avg_queue_length_meters, max_queue_length_meters, avg_congestion_index
                ) VALUES (
                    :bucket_15m, :segment_id, :source_mode, 15, :avg_speed_kmh,
                    :p85_speed_kmh, :total_flow_veh, :avg_occupancy_percent,
                    :avg_queue_length_meters, :max_queue_length_meters, :avg_congestion_index
                ) ON CONFLICT (bucket_15m, segment_id, source_mode) DO NOTHING;
            """)
        else:
            insert_stmt = text("""
                INSERT OR IGNORE INTO traffic_15m_aggregates (
                    bucket_15m, segment_id, source_mode, sample_count, avg_speed_kmh,
                    p85_speed_kmh, total_flow_veh, avg_occupancy_percent,
                    avg_queue_length_meters, max_queue_length_meters, avg_congestion_index
                ) VALUES (
                    :bucket_15m, :segment_id, :source_mode, 15, :avg_speed_kmh,
                    :p85_speed_kmh, :total_flow_veh, :avg_occupancy_percent,
                    :avg_queue_length_meters, :max_queue_length_meters, :avg_congestion_index
                );
            """)

        # Generate 24 fifteen-minute buckets (6 hours)
        for i in range(24):
            bucket_time = now_utc - timedelta(minutes=i * 15)
            # Align to 15-minute boundary
            minute = (bucket_time.minute // 15) * 15
            aligned_dt = bucket_time.replace(minute=minute, second=0, microsecond=0)
            bucket_val = aligned_dt if is_pg else aligned_dt.isoformat()

            # Time of day speed variation
            hour = aligned_dt.hour
            is_rush = 8 <= hour <= 10 or 17 <= hour <= 20
            base_speed = 28.5 if is_rush else 42.0
            base_flow = 2200.0 if is_rush else 1250.0

            for seg_id in segments:
                speed = base_speed + (hash(seg_id + str(i)) % 7) - 3.5
                # Empirical 85th percentile across 15 synthetic sample speeds
                samples = [speed + ((-1.5 + j * 0.2) if j % 2 == 0 else (1.5 - j * 0.2)) for j in range(15)]
                sorted_samples = sorted(samples)
                # For n=15: k = 14 * 0.85 = 11.9 -> index 11 (weight 0.1) and index 12 (weight 0.9)
                p85_calc = round(sorted_samples[11] * 0.1 + sorted_samples[12] * 0.9, 2)

                # Total vehicle volume for 15-minute bucket: q * 0.25
                total_veh = round(((base_flow + (hash(seg_id) % 300) - 150) * 0.25), 1)

                await session.execute(insert_stmt, {
                    "bucket_15m": bucket_val,
                    "segment_id": seg_id,
                    "source_mode": "SIMULATION",
                    "avg_speed_kmh": round(speed, 2),
                    "p85_speed_kmh": p85_calc,
                    "total_flow_veh": total_veh,
                    "avg_occupancy_percent": round(max(15.0, min(80.0, (1.0 - speed / 50.0) * 70.0)), 1),
                    "avg_queue_length_meters": round(max(5.0, (1.0 - speed / 50.0) * 60.0), 1),
                    "max_queue_length_meters": round(max(10.0, (1.0 - speed / 50.0) * 85.0), 1),
                    "avg_congestion_index": round(max(0.1, min(0.9, (1.0 - speed / 50.0))), 3)
                })
                count += 1

        await session.commit()
        logger.info("Seeded %d historical 15m continuous aggregate records.", count)
        return count


# Singleton service instance
continuous_aggregator = ContinuousAggregatorService()
