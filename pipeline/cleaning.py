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


class DataCleaner(BaseEstimator, TransformerMixin):
    """Convierte datos de bronze en silver.

    - Elimina columnas sin uso.
    - Renombra las clases del target.
    - Imputa arrival_delay_in_minutes con la mediana de su grupo de
      departure_delay_in_minutes (la ausencia es MAR respecto de departure_delay).

    Las medianas se aprenden solo sobre train (fit) y se aplican a train y test (transform):

        cleaner = DataCleaner().fit(bronze_train)
        silver_train = cleaner.transform(bronze_train)
        silver_test = cleaner.transform(bronze_test)
    """

    def __init__(self, bins=DEPARTURE_DELAY_BINS):
        self.bins = bins

    def fit(self, X: pd.DataFrame, y=None):
        self.medians_ = X.groupby(self._groups(X), observed=True)[
            ARRIVAL_DELAY_COLUMN
        ].median()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.drop(columns=DROP_COLUMNS, errors="ignore")
        if TARGET in X.columns:
            X[TARGET] = X[TARGET].replace(TARGET_RENAME)
        conditional_medians = self._groups(X).astype("object").map(self.medians_)
        X[ARRIVAL_DELAY_COLUMN] = (
            X[ARRIVAL_DELAY_COLUMN].fillna(conditional_medians).astype("float64")
        )
        return X

    def _groups(self, X: pd.DataFrame) -> pd.Series:
        return pd.cut(X[DEPARTURE_DELAY_COLUMN], bins=self.bins)
