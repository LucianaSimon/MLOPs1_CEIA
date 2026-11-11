"""Gold -> Modelo: Random Forest de satisfacción, validación cruzada y evaluación."""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, fbeta_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from pipeline.config import (
    CV_SPLITS,
    FEATURES,
    NOMINAL_FEATURES,
    NUMERIC_FEATURES,
    ORDINAL_FEATURES,
    POS_LABEL,
    RANDOM_STATE,
    RATED_FEATURES,
    TARGET,
)


class SatisfactionClassifier:
    """Random Forest que predice la satisfacción a partir de datos de gold.

    Recibe DataFrames de gold completos (con id y target) y separa X e y internamente:

        classifier = SatisfactionClassifier()
        cv_metrics = classifier.cross_validate(gold_train)
        classifier.fit(gold_train)
        test_metrics = classifier.evaluate(gold_test)
    """

    def __init__(self, random_state: int = RANDOM_STATE, cv_splits: int = CV_SPLITS):
        self.random_state = random_state
        self.cv_splits = cv_splits
        self.pipeline = self._build_pipeline()

    def fit(self, df: pd.DataFrame) -> "SatisfactionClassifier":
        X, y = self._split_xy(df)
        self.pipeline.fit(X, y)
        return self

    def predict(self, df: pd.DataFrame):
        return self.pipeline.predict(df[FEATURES])

    def logged_params(self) -> dict[str, str]:
        """Hiperparámetros del Random Forest y datos de la validación cruzada."""
        model = self.pipeline.named_steps["model"]
        params = {
            "estimator": type(model).__name__,
            "cv_splits": str(self.cv_splits),
            "pos_label": POS_LABEL,
        }
        params.update({f"rf_{key}": str(value) for key, value in model.get_params().items()})
        return params

    def evaluate(self, df: pd.DataFrame) -> dict:
        """Métricas del modelo ya entrenado sobre df."""
        _, y = self._split_xy(df)
        return self._metrics(y, self.predict(df))

    def cross_validate(self, df: pd.DataFrame) -> dict:
        """Métricas de validación cruzada estratificada. No modifica el modelo entrenado."""
        X, y = self._split_xy(df)
        cv = StratifiedKFold(
            n_splits=self.cv_splits, shuffle=True, random_state=self.random_state
        )
        y_pred = cross_val_predict(self._build_pipeline(), X, y, cv=cv)
        return self._metrics(y, y_pred)

    def _build_pipeline(self) -> Pipeline:
        preprocessor = ColumnTransformer(
            [
                ("numeric", "passthrough", NUMERIC_FEATURES),
                ("service", "passthrough", ORDINAL_FEATURES),
                (
                    "nominal",
                    OneHotEncoder(handle_unknown="ignore", drop="first"),
                    NOMINAL_FEATURES,
                ),
                ("service_indicators", "passthrough", RATED_FEATURES),
            ]
        )
        return Pipeline(
            [
                ("preprocessor", preprocessor),
                ("model", RandomForestClassifier(random_state=self.random_state)),
            ]
        )

    @staticmethod
    def _split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        return df[FEATURES], df[TARGET]

    @staticmethod
    def _metrics(y_true, y_pred) -> dict:
        return {
            "fbeta_0.5": fbeta_score(y_true, y_pred, beta=0.5, pos_label=POS_LABEL),
            "f1": f1_score(y_true, y_pred, pos_label=POS_LABEL),
            "precision": precision_score(y_true, y_pred, pos_label=POS_LABEL),
            "recall": recall_score(y_true, y_pred, pos_label=POS_LABEL),
        }
