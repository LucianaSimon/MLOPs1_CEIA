"""Silver -> Gold: selección de features e indicadores de servicio calificado."""

import pandas as pd

from pipeline.config import FEATURES, ID_COLUMN, ORDINAL_FEATURES, RATED_FEATURES, TARGET


def to_gold(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el dataset listo para el modelo: id, features seleccionadas y target."""
    df = df.copy()
    for col, rated_col in zip(ORDINAL_FEATURES, RATED_FEATURES):
        df[rated_col] = (df[col] > 0).astype(int)
    return df[[ID_COLUMN] + FEATURES + [TARGET]]
