"""Silver -> Gold: selección de features e indicadores de servicio calificado."""

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from pipeline.config import (
    FEATURES,
    ID_COLUMN,
    ORDINAL_FEATURES,
    RATED_FEATURES,
    TARGET,
)


class FeatureBuilder(BaseEstimator, TransformerMixin):
    """Convierte datos de silver en gold, listos para el modelo.

    - Agrega por cada servicio una columna <servicio>_rated: 1 si fue calificado
      (valor > 0), 0 si no aplica.
    - Deja solo id, las features seleccionadas y el target.

    No aprende nada de los datos, por lo que fit no hace nada:

        gold_train = FeatureBuilder().transform(silver_train)
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col, rated_col in zip(ORDINAL_FEATURES, RATED_FEATURES):
            X[rated_col] = (X[col] > 0).astype(int)
        return X[[ID_COLUMN] + FEATURES + [TARGET]]
