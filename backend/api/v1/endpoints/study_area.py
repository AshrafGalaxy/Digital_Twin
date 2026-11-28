"""
study_area.py

Endpoints for querying the authoritative study-area boundary geometry
with in-memory caching and HTTP ETag / If-None-Match revalidation.
"""

from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
import threading
from typing import Any, Dict, Optional
from fastapi import APIRouter, Header, HTTPException, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study-area", tags=["Study Area"])

STUDY_AREA_PATH = Path("data/study_area.geojson")
FALLBACK_PATH = Path("../data/study_area.geojson")
CACHE_CONTROL_HEADER = "public, max-age=300, must-revalidate"


@dataclass(frozen=True)
class _StudyAreaCacheEntry:
    path_key: str
    mtime_ns: int
    size: int
    body_bytes: bytes
    etag: str


_cache_lock = threading.Lock()
_cached_entry: Optional[_StudyAreaCacheEntry] = None


def clear_study_area_cache() -> None:
    """Clears the cached study-area geometry entry (primarily for test isolation)."""
    global _cached_entry
    with _cache_lock:
        _cached_entry = None


def _etag_matches(if_none_match: Optional[str], current_etag: str) -> bool:
    """Evaluates RFC 9110 weak/exact ETag matching against an If-None-Match header."""
    if not if_none_match:
        return False
    normalized_target = current_etag.strip()
    for raw_tag in if_none_match.split(","):
        candidate = raw_tag.strip()
        if not candidate:
            continue
        if candidate == "*":
            return True
        if candidate.startswith("W/"):
            candidate = candidate[2:].strip()
        if candidate == normalized_target:
            return True
    return False


def _load_study_area_cached(path: Path) -> _StudyAreaCacheEntry:
    """
    Returns cached UTF-8 JSON bytes and ETag for the resolved study-area file,
    reloading only on cold start or when file metadata (path, mtime, size) changes.
    """
    global _cached_entry
    try:
        resolved_key = str(path.resolve())
        stat_res = path.stat()
        mtime_ns = int(stat_res.st_mtime_ns)
        size = int(stat_res.st_size)

        with _cache_lock:
            entry = _cached_entry
            if (
                entry is not None
                and entry.path_key == resolved_key
                and entry.mtime_ns == mtime_ns
                and entry.size == size
            ):
                return entry

            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            body_bytes = json.dumps(
                payload, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            etag = f'"{hashlib.sha256(body_bytes).hexdigest()[:32]}"'
            new_entry = _StudyAreaCacheEntry(
                path_key=resolved_key,
                mtime_ns=mtime_ns,
                size=size,
                body_bytes=body_bytes,
                etag=etag,
            )
            _cached_entry = new_entry
            return new_entry
    except Exception as exc:
        logger.error("Failed reading study area file at %s: %s", path, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load study area geometry.")


@router.get("", response_model=Dict[str, Any])
async def get_study_area_geojson(
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
) -> Response:
    path = STUDY_AREA_PATH if STUDY_AREA_PATH.exists() else FALLBACK_PATH
    if not path.exists():
        raise HTTPException(status_code=404, detail="Study area GeoJSON not found on server")

    entry = _load_study_area_cached(path)
    headers = {
        "ETag": entry.etag,
        "Cache-Control": CACHE_CONTROL_HEADER,
    }
    if _etag_matches(if_none_match, entry.etag):
        return Response(status_code=304, headers=headers)

    return Response(
        content=entry.body_bytes,
        status_code=200,
        media_type="application/json",
        headers=headers,
    )
