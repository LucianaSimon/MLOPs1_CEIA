"""Lectura y escritura de tablas en Postgres."""

import os

import pandas as pd
from sqlalchemy import create_engine


class Database:
    """Conexión a Postgres configurada por variables de entorno.

        db = Database()
        df = db.read("bronze", "passenger_satisfaction_train", order_by="raw_id")
        db.write(df, "silver", "passenger_satisfaction_train")
    """

    def __init__(self):
        user = os.environ["POSTGRES_USER"]
        password = os.environ["POSTGRES_PASSWORD"]
        host = os.environ.get("POSTGRES_HOST", "postgres")
        port = os.environ.get("POSTGRES_PORT", "5432")
        name = os.environ["POSTGRES_DB"]
        self.engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
        )

    def read(self, schema: str, table: str, order_by: str | None = None) -> pd.DataFrame:
        # El orden de filas es determinístico para que el entrenamiento sea reproducible
        query = f"SELECT * FROM {schema}.{table}"
        if order_by:
            query += f" ORDER BY {order_by}"
        return pd.read_sql_query(query, self.engine)

    def write(self, df: pd.DataFrame, schema: str, table: str) -> None:
        df.to_sql(
            table,
            self.engine,
            schema=schema,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=5000,
        )
