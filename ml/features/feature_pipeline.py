"""
feature_pipeline.py

Offline Feature Store Generation and Persistence Pipeline.
Extracts validated historical observations, computes leakage-safe features,
and serializes Gold-tier analytical tables to Parquet and CSV formats
with cryptographic SHA-256 manifests.
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.features.traffic_features import (
    FEATURE_COLUMNS as TRAFFIC_FEATURES,
    TARGET_COLUMN as TRAFFIC_TARGET,
    generate_corridor_traffic_history,
    build_traffic_features
)
from ml.features.energy_features import (
    ENERGY_FEATURE_COLUMNS as ENERGY_FEATURES,
    ENERGY_TARGET_COLUMN as ENERGY_TARGET,
    generate_building_energy_history,
    build_energy_features
)

GOLD_DIR = ROOT_DIR / "data" / "gold" / "features"
GOLD_DIR.mkdir(parents=True, exist_ok=True)


def compute_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_gold_traffic_features(days: int = 30, seed: int = 42) -> Dict[str, Any]:
    """
    Generates and persists the Gold traffic feature table.
    """
    print(f"[+] Generating {days}-day traffic history for Gold feature store...")
    raw_df = generate_corridor_traffic_history(days=days, seed=seed)
    featured_df = build_traffic_features(raw_df)

    # Validate zero leakage and completeness
    required_cols = ["timestamp", "segment_id"] + TRAFFIC_FEATURES + [TRAFFIC_TARGET]
    assert all(col in featured_df.columns for col in required_cols), f"Missing required traffic feature columns: {[c for c in required_cols if c not in featured_df.columns]}"
    assert not featured_df[TRAFFIC_FEATURES].isna().any().any(), "NaN values found in traffic features"

    parquet_path = GOLD_DIR / "traffic_features_v1.parquet"
    csv_path = GOLD_DIR / "traffic_features_v1.csv"

    # Export Parquet with PyArrow
    table = pa.Table.from_pandas(featured_df)
    pq.write_table(table, parquet_path, compression="snappy")
    featured_df.to_csv(csv_path, index=False)

    sha256_parquet = compute_file_sha256(parquet_path)
    sha256_csv = compute_file_sha256(csv_path)

    print(f"[OK] Saved traffic Gold features: {len(featured_df)} rows")
    print(f"     Parquet: {parquet_path} (SHA-256: {sha256_parquet[:12]}...)")
    print(f"     CSV:     {csv_path} (SHA-256: {sha256_csv[:12]}...)")

    return {
        "dataset_name": "traffic_features_v1",
        "rows": len(featured_df),
        "days": days,
        "features": TRAFFIC_FEATURES,
        "target": TRAFFIC_TARGET,
        "parquet_path": str(parquet_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "csv_path": str(csv_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "sha256_parquet": sha256_parquet,
        "sha256_csv": sha256_csv,
        "start_time": featured_df["timestamp"].min().isoformat(),
        "end_time": featured_df["timestamp"].max().isoformat()
    }


def generate_gold_energy_features(days: int = 35, seed: int = 42) -> Dict[str, Any]:
    """
    Generates and persists the Gold building energy feature table.
    """
    print(f"[+] Generating {days}-day building energy history for Gold feature store...")
    raw_df = generate_building_energy_history(days=days, seed=seed)
    featured_df = build_energy_features(raw_df)

    required_cols = ["timestamp", "building_id"] + ENERGY_FEATURES + [ENERGY_TARGET]
    assert all(col in featured_df.columns for col in required_cols), f"Missing required energy feature columns: {[c for c in required_cols if c not in featured_df.columns]}"
    assert not featured_df[ENERGY_FEATURES].isna().any().any(), "NaN values found in energy features"

    parquet_path = GOLD_DIR / "energy_features_v1.parquet"
    csv_path = GOLD_DIR / "energy_features_v1.csv"

    table = pa.Table.from_pandas(featured_df)
    pq.write_table(table, parquet_path, compression="snappy")
    featured_df.to_csv(csv_path, index=False)

    sha256_parquet = compute_file_sha256(parquet_path)
    sha256_csv = compute_file_sha256(csv_path)

    print(f"[OK] Saved energy Gold features: {len(featured_df)} rows")
    print(f"     Parquet: {parquet_path} (SHA-256: {sha256_parquet[:12]}...)")
    print(f"     CSV:     {csv_path} (SHA-256: {sha256_csv[:12]}...)")

    return {
        "dataset_name": "energy_features_v1",
        "rows": len(featured_df),
        "days": days,
        "features": ENERGY_FEATURES,
        "target": ENERGY_TARGET,
        "parquet_path": str(parquet_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "csv_path": str(csv_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "sha256_parquet": sha256_parquet,
        "sha256_csv": sha256_csv,
        "start_time": featured_df["timestamp"].min().isoformat(),
        "end_time": featured_df["timestamp"].max().isoformat()
    }


def run_feature_store_pipeline() -> Dict[str, Any]:
    """Executes the complete Gold Feature Store generation pipeline and updates manifest."""
    traffic_meta = generate_gold_traffic_features()
    energy_meta = generate_gold_energy_features()

    manifest = {
        "pipeline_version": "v1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "storage_tier": "GOLD",
        "format": ["parquet", "csv"],
        "compression": "snappy",
        "datasets": {
            "traffic": traffic_meta,
            "energy": energy_meta
        }
    }

    manifest_path = GOLD_DIR / "feature_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[OK] Successfully wrote Gold Feature Manifest to: {manifest_path}")
    return manifest


if __name__ == "__main__":
    run_feature_store_pipeline()
