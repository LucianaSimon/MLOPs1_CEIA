"""Ejecuta el pipeline medallion completo: bronze -> silver -> gold -> modelo.

    python -m pipeline.run
"""

import json
import os
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from mlflow.models import infer_signature

from pipeline.cleaning import DataCleaner
from pipeline.config import FEATURES
from pipeline.database import Database
from pipeline.features import FeatureBuilder
from pipeline.training import SatisfactionClassifier

EXPERIMENT = "passenger_satisfaction"

TABLES = {
    "train": "passenger_satisfaction_train",
    "test": "passenger_satisfaction_test",
}


class MedallionPipeline:
    """Lee bronze, escribe silver y gold, entrena el modelo y guarda los artefactos.

    Artefactos en artifacts_dir:
    - model.joblib: DataCleaner (con las medianas de train), FeatureBuilder y
      SatisfactionClassifier entrenado, para aplicar sobre datos nuevos de bronze.
    - metrics.json: métricas de validación cruzada y de test.

    Si MLFLOW_TRACKING_URI está definido, la misma corrida queda como un
    experimento: hiperparámetros del Random Forest, métricas y el modelo.
    """

    def __init__(self, db: Database, artifacts_dir: Path):
        self.db = db
        self.artifacts_dir = artifacts_dir
        self.cleaner = DataCleaner()
        self.builder = FeatureBuilder()
        self.classifier = SatisfactionClassifier()

    def run(self) -> dict:
        bronze = {
            split: self.db.read("bronze", table, order_by="raw_id")
            for split, table in TABLES.items()
        }

        self.cleaner.fit(bronze["train"])
        silver = {split: self.cleaner.transform(df) for split, df in bronze.items()}
        self._write("silver", silver)

        gold = {split: self.builder.transform(df) for split, df in silver.items()}
        self._write("gold", gold)

        metrics = {"cross_validation": self.classifier.cross_validate(gold["train"])}
        self.classifier.fit(gold["train"])
        metrics["test"] = self.classifier.evaluate(gold["test"])

        self._save(metrics)
        self._log_experiment(metrics, gold["train"])
        return metrics

    def _write(self, schema: str, data: dict) -> None:
        for split, df in data.items():
            self.db.write(df, schema, TABLES[split])
            print(f"{schema}.{TABLES[split]}: {len(df)} filas")

    def _save(self, metrics: dict) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "cleaner": self.cleaner,
                "builder": self.builder,
                "classifier": self.classifier,
            },
            self.artifacts_dir / "model.joblib",
        )
        (self.artifacts_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    def _log_experiment(self, metrics: dict, train: pd.DataFrame) -> None:
        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
        if not tracking_uri:
            print("MLFLOW_TRACKING_URI no está definido: no se registra el experimento")
            return

        sample = train.head(20)
        signature = infer_signature(sample[FEATURES], self.classifier.predict(sample))
        flat_metrics = {
            f"{split}_{name}": float(value)
            for split, values in metrics.items()
            for name, value in values.items()
        }

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(EXPERIMENT)
        with mlflow.start_run():
            mlflow.log_params(self.classifier.logged_params())
            mlflow.log_metrics(flat_metrics)
            mlflow.sklearn.log_model(
                self.classifier.pipeline,
                name="satisfaction_model",
                signature=signature,
                input_example=sample[FEATURES],
                serialization_format="cloudpickle",
                registered_model_name=EXPERIMENT,
            )
            mlflow.log_artifact(self.artifacts_dir / "model.joblib")
            print(f"Experimento {EXPERIMENT} registrado en {tracking_uri}")


if __name__ == "__main__":
    artifacts_dir = Path(os.environ.get("ARTIFACTS_DIR", "artifacts"))
    metrics = MedallionPipeline(Database(), artifacts_dir).run()
    print(json.dumps(metrics, indent=2))
