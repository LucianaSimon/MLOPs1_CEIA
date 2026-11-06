"""Bronze -> Silver: limpieza, imputación de faltantes y normalización del target."""

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from pipeline.config import (
    ARRIVAL_DELAY_COLUMN,
    DEPARTURE_DELAY_BINS,
    DEPARTURE_DELAY_COLUMN,
    DROP_COLUMNS,
    TARGET,
    TARGET_RENAME,
)


class ConditionalMedianImputer(BaseEstimator, TransformerMixin):
    """Imputa arrival_delay_in_minutes con la mediana de su grupo de departure_delay_in_minutes.

    La ausencia de arrival_delay es MAR respecto de departure_delay, por eso la mediana
    se calcula por grupo. Las medianas se aprenden solo sobre train y se aplican
    a train y test.
    """

    def __init__(self, bins=DEPARTURE_DELAY_BINS):
        self.bins = bins

    def _groups(self, X: pd.DataFrame) -> pd.Series:
        return pd.cut(X[DEPARTURE_DELAY_COLUMN], bins=self.bins)

    def fit(self, X: pd.DataFrame, y=None):
        self.medians_ = X.groupby(self._groups(X), observed=True)[
            ARRIVAL_DELAY_COLUMN
        ].median()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        conditional_medians = self._groups(X).astype("object").map(self.medians_)
        X[ARRIVAL_DELAY_COLUMN] = (
            X[ARRIVAL_DELAY_COLUMN].fillna(conditional_medians).astype("float64")
        )
        return X


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina columnas sin uso y renombra las clases del target."""
    df = df.drop(columns=DROP_COLUMNS, errors="ignore")
    df[TARGET] = df[TARGET].replace(TARGET_RENAME)
    return df


def to_silver(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, ConditionalMedianImputer]:
    """Limpia train y test, imputando faltantes con medianas aprendidas solo en train."""
    train, test = clean(train), clean(test)
    imputer = ConditionalMedianImputer().fit(train)
    return imputer.transform(train), imputer.transform(test), imputer
