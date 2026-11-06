"""Gold -> Modelo: pipeline de Random Forest, validación cruzada y evaluación."""

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


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer([
        ("numeric", "passthrough", NUMERIC_FEATURES),
        ("service", "passthrough", ORDINAL_FEATURES),
        ("nominal", OneHotEncoder(handle_unknown="ignore", drop="first"), NOMINAL_FEATURES),
        ("service_indicators", "passthrough", RATED_FEATURES),
    ])
    return Pipeline([
        ("preprocessor", preprocessor),
        ("model", RandomForestClassifier(random_state=RANDOM_STATE)),
    ])


def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[FEATURES], df[TARGET]


def eval_metrics(y_true, y_pred, pos_label=POS_LABEL) -> dict:
    return {
        "fbeta_0.5": fbeta_score(y_true, y_pred, beta=0.5, pos_label=pos_label),
        "f1": f1_score(y_true, y_pred, pos_label=pos_label),
        "precision": precision_score(y_true, y_pred, pos_label=pos_label),
        "recall": recall_score(y_true, y_pred, pos_label=pos_label),
    }


def cross_validate(train: pd.DataFrame) -> dict:
    X, y = split_xy(train)
    cv = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    y_pred = cross_val_predict(build_pipeline(), X, y, cv=cv)
    return eval_metrics(y, y_pred)


def train(train: pd.DataFrame) -> Pipeline:
    X, y = split_xy(train)
    return build_pipeline().fit(X, y)


def evaluate(model: Pipeline, test: pd.DataFrame) -> dict:
    X, y = split_xy(test)
    return eval_metrics(y, model.predict(X))
