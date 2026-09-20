"""
mlflow_tracker.py

MLflow Experiment Tracking and Model Registry Manager.
Configures local file-store tracking in `artifacts/mlflow/`,
logging training hyperparameters, chronological split metadata,
evaluation metrics, baseline comparisons, and serialized model artifacts.
"""

import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MLFLOW_TRACKING_DIR = ROOT_DIR / "artifacts" / "mlflow"
MLFLOW_TRACKING_DIR.mkdir(parents=True, exist_ok=True)

import mlflow

os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"


class MLflowTracker:
    """
    Manages structured experiment runs, metric logging, and artifact storage
    using local file-backed MLflow registry adhering to §15.1 and §16.1.
    """

    def __init__(self, experiment_name: str = "SmartCity_DigitalTwin"):
        self.experiment_name = experiment_name
        # Use sqlite backend in artifacts/mlflow/ for full MLflow 3.x support
        db_path = (MLFLOW_TRACKING_DIR / "mlflow.db").resolve().as_posix()
        tracking_uri = f"sqlite:///{db_path}"
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)

    def log_training_run(
        self,
        run_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        tags: Dict[str, str],
        artifact_paths: Optional[Dict[str, Path]] = None,
        feature_names: Optional[list] = None
    ) -> str:
        """
        Executes a formal MLflow tracking run, recording all §15.1 mandatory fields.
        Returns the unique MLflow run_id.
        """
        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id

            # 1. Log Hyperparameters & Config
            for k, v in parameters.items():
                if isinstance(v, (list, dict)):
                    mlflow.log_param(k, json.dumps(v)[:250])
                else:
                    mlflow.log_param(k, v)

            # 2. Log Evaluation & Baseline Comparison Metrics
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    mlflow.log_metric(k, float(v))

            # 3. Log Governance & Locality Tags
            mlflow.set_tags(tags)
            mlflow.set_tag("registry_status", "APPROVED_FOR_DEMO")
            mlflow.set_tag("schema_version", "v1")

            # 4. Log Feature Schema Artifact
            if feature_names:
                schema_dict = {
                    "feature_count": len(feature_names),
                    "features": feature_names
                }
                mlflow.log_dict(schema_dict, "feature_schema.json")

            # 5. Log Model Artifacts
            if artifact_paths:
                for name, path in artifact_paths.items():
                    if path.exists():
                        mlflow.log_artifact(str(path), artifact_path="model_package")

            print(f"[MLflow] Logged run '{run_name}' -> Run ID: {run_id}")
            return run_id
