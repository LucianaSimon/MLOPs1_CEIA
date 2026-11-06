"""Ejecuta el pipeline medallion completo: bronze -> silver -> gold -> modelo.

    python -m pipeline.run
"""

import json
import os
from pathlib import Path

import joblib

from pipeline.cleaning import DataCleaner
from pipeline.database import Database
from pipeline.features import FeatureBuilder
from pipeline.training import SatisfactionClassifier

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


if __name__ == "__main__":
    artifacts_dir = Path(os.environ.get("ARTIFACTS_DIR", "artifacts"))
    metrics = MedallionPipeline(Database(), artifacts_dir).run()
    print(json.dumps(metrics, indent=2))
