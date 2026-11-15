"""
test_evaluation_benchmarks.py

Hermetic regression tests for model evaluation benchmarking and experiment E-03 schema harmony.
Verifies:
1. Experiment E-03 schema conformance and single-source-of-truth delegation.
2. Defensive guards against missing model artifacts (clean exit 1 with descriptive stderr).
3. Preservation of existing evaluation_benchmarks.json when artifact errors occur.
4. Harmonized schema parity between ablation_study.py and run_evaluation_benchmarks.py.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.features.traffic_features import FEATURE_COLUMNS, TARGET_COLUMN
from ml.training.ablation_study import run_ablation_study, FEATURE_CONFIGS
from scripts.run_evaluation_benchmarks import (
    verify_required_artifacts,
    run_experiment_e01_traffic,
    run_experiment_e02_energy,
    run_experiment_e03_ablation,
    main as run_benchmarks_main,
)


REQUIRED_E03_CONFIG_KEYS = [
    "featureCount",
    "features",
    "testMaeKmh",
    "testRmseKmh",
    "improvementVsBaselinePct",
]

REQUIRED_E03_ROOT_KEYS = [
    "experimentId",
    "title",
    "executedAt",
    "baselinePersistenceMae",
    "configurations",
]


def _build_dummy_traffic_feature_df(n_rows: int = 50) -> pd.DataFrame:
    """Build a deterministic dummy dataframe with all required traffic features."""
    data = {
        TARGET_COLUMN: [25.0 + float(i % 10) for i in range(n_rows)],
        "speed_kmh": [24.0 + float(i % 10) for i in range(n_rows)],
    }
    for col in FEATURE_COLUMNS:
        data[col] = [10.0 + float(i % 5) for i in range(n_rows)]
    return pd.DataFrame(data)


def test_ablation_study_payload_schema_keys():
    """Verify that run_ablation_study produces the authoritative E-03 schema and keys."""
    dummy_df = _build_dummy_traffic_feature_df(60)

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([25.0] * 6)

    with patch("ml.training.ablation_study.pd.read_parquet", return_value=dummy_df), \
         patch("ml.training.ablation_study.XGBRegressor", return_value=mock_model):
        res = run_ablation_study(seed=42, update_benchmarks_file=False)

    for k in REQUIRED_E03_ROOT_KEYS:
        assert k in res, f"Missing root key '{k}' in E-03 payload"

    assert res["experimentId"] == "E-03"
    assert res["title"] == "Traffic Feature Ablation Study"
    assert isinstance(res["baselinePersistenceMae"], (int, float))
    assert isinstance(res["configurations"], dict)

    for cfg_name in FEATURE_CONFIGS.keys():
        assert cfg_name in res["configurations"], f"Missing configuration '{cfg_name}'"
        cfg_data = res["configurations"][cfg_name]
        for ck in REQUIRED_E03_CONFIG_KEYS:
            assert ck in cfg_data, f"Missing config key '{ck}' in '{cfg_name}'"


def test_run_experiment_e03_ablation_delegates_to_ablation_study():
    """Verify that run_experiment_e03_ablation delegates directly to run_ablation_study."""
    mock_payload = {
        "experimentId": "E-03",
        "title": "Traffic Feature Ablation Study",
        "executedAt": "2026-11-15T00:00:00+00:00",
        "baselinePersistenceMae": 4.25,
        "configurations": {
            "Config-1 (Lags Only)": {
                "featureCount": 5,
                "features": ["speed_lag_5m"],
                "testMaeKmh": 3.8,
                "testRmseKmh": 5.1,
                "improvementVsBaselinePct": 12.0,
            }
        },
    }

    with patch("ml.training.ablation_study.run_ablation_study", return_value=mock_payload) as mock_run:
        result = run_experiment_e03_ablation()
        mock_run.assert_called_once_with(seed=42, update_benchmarks_file=False)
        assert result == mock_payload


def test_verify_required_artifacts_missing_traffic_exits_nonzero(capsys):
    """Verify verify_required_artifacts exits with code 1 when traffic_xgb_v1.joblib is absent."""
    with patch("scripts.run_evaluation_benchmarks.CorridorForecaster") as mock_fc_cls:
        instance = MagicMock()
        instance.traffic_artifact = None
        instance.energy_artifact = {"model": MagicMock()}
        mock_fc_cls.return_value = instance

        with pytest.raises(SystemExit) as exc_info:
            verify_required_artifacts()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "traffic_xgb_v1.joblib" in captured.err


def test_verify_required_artifacts_missing_energy_exits_nonzero(capsys):
    """Verify verify_required_artifacts exits with code 1 when energy_xgb_v1.joblib is absent."""
    with patch("scripts.run_evaluation_benchmarks.CorridorForecaster") as mock_fc_cls:
        instance = MagicMock()
        instance.traffic_artifact = {"model": MagicMock()}
        instance.energy_artifact = None
        mock_fc_cls.return_value = instance

        with pytest.raises(SystemExit) as exc_info:
            verify_required_artifacts()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "energy_xgb_v1.joblib" in captured.err


def test_run_experiment_e01_missing_artifact_exits_nonzero(capsys):
    """Verify run_experiment_e01_traffic exits cleanly with code 1 on missing model."""
    with patch("scripts.run_evaluation_benchmarks.CorridorForecaster") as mock_fc_cls:
        instance = MagicMock()
        instance.traffic_artifact = None
        mock_fc_cls.return_value = instance

        with pytest.raises(SystemExit) as exc_info:
            run_experiment_e01_traffic()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "traffic_xgb_v1.joblib" in captured.err


def test_run_experiment_e02_missing_artifact_exits_nonzero(capsys):
    """Verify run_experiment_e02_energy exits cleanly with code 1 on missing model."""
    with patch("scripts.run_evaluation_benchmarks.CorridorForecaster") as mock_fc_cls:
        instance = MagicMock()
        instance.energy_artifact = None
        mock_fc_cls.return_value = instance

        with pytest.raises(SystemExit) as exc_info:
            run_experiment_e02_energy()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "energy_xgb_v1.joblib" in captured.err


def test_missing_artifact_preserves_existing_benchmark_file(tmp_path, monkeypatch):
    """Verify that a missing artifact halts execution before writing or corrupting evaluation_benchmarks.json."""
    fake_benchmarks = tmp_path / "evaluation_benchmarks.json"
    initial_content = {"existing": "untouched_data", "timestamp": "2026-01-01T00:00:00+00:00"}
    fake_benchmarks.write_text(json.dumps(initial_content), encoding="utf-8")

    monkeypatch.setattr("scripts.run_evaluation_benchmarks.BASE_DIR", tmp_path.parent)
    with patch("scripts.run_evaluation_benchmarks.CorridorForecaster") as mock_fc_cls:
        instance = MagicMock()
        instance.traffic_artifact = None
        mock_fc_cls.return_value = instance

        with pytest.raises(SystemExit) as exc_info:
            run_benchmarks_main()

        assert exc_info.value.code == 1

    # Verify initial file remains unmodified
    assert fake_benchmarks.exists()
    saved = json.loads(fake_benchmarks.read_text(encoding="utf-8"))
    assert saved == initial_content


def test_ablation_study_file_update_schema_parity(tmp_path, monkeypatch):
    """Verify that update_benchmarks_file=True updates both root E-03 and experiments[E-03_feature_ablation]."""
    test_file = tmp_path / "evaluation_benchmarks.json"
    initial_data = {
        "timestamp": "2026-11-15T00:00:00+00:00",
        "experiments": {"E-01_traffic_forecast": {"persistence_mae": 4.2}},
    }
    test_file.write_text(json.dumps(initial_data), encoding="utf-8")

    monkeypatch.setattr("ml.training.ablation_study.BENCHMARKS_FILE", test_file)

    dummy_df = _build_dummy_traffic_feature_df(60)
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([25.0] * 6)

    with patch("ml.training.ablation_study.pd.read_parquet", return_value=dummy_df), \
         patch("ml.training.ablation_study.XGBRegressor", return_value=mock_model):
        res = run_ablation_study(seed=42, update_benchmarks_file=True)

    loaded = json.loads(test_file.read_text(encoding="utf-8"))
    assert "E-03" in loaded
    assert "experiments" in loaded
    assert "E-03_feature_ablation" in loaded["experiments"]

    # Both must match the returned payload exactly
    assert loaded["E-03"] == res
    assert loaded["experiments"]["E-03_feature_ablation"] == res
    # Preserves existing experiment records
    assert loaded["experiments"]["E-01_traffic_forecast"]["persistence_mae"] == 4.2
