import joblib
import mlflow
import pandas as pd
import os

from mlflow.tracking import MlflowClient
from pipeline.config import FEATURES
from pipeline.database import Database


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

MLFLOW_URI = os.environ.get(
    "MLFLOW_TRACKING_URI",
    "http://localhost:5000"
)
MODEL_NAME = "passenger_satisfaction"
MODEL_VERSION = "1"

mlflow.set_tracking_uri(MLFLOW_URI)


# ============================================================
# 2. RECUPERAR MODELO Y TRANSFORMADORES DESDE MLFLOW
# ============================================================

client = MlflowClient()

version = client.get_model_version(
    name=MODEL_NAME,
    version=MODEL_VERSION
)

print("Versión del modelo:", version.version)
print("ID del entrenamiento:", version.run_id)

# Recuperar Random Forest
modelo = mlflow.sklearn.load_model(
    f"models:/{MODEL_NAME}/{MODEL_VERSION}"
)

# Descargar los transformadores del mismo entrenamiento
ruta_artefactos = mlflow.artifacts.download_artifacts(
    run_id=version.run_id,
    artifact_path="model.joblib"
)

artefactos = joblib.load(ruta_artefactos)

cleaner = artefactos["cleaner"]
builder = artefactos["builder"]

print("Modelo y transformadores recuperados correctamente")


# ============================================================
# 3. LEER PASAJEROS NUEVOS DESDE POSTGRESQL
# ============================================================

db = Database()

pasajeros = db.read(
    "bronze",
    "passenger_satisfaction_predict"
)

print("Pasajeros recuperados:", len(pasajeros))


# ============================================================
# 4. TRANSFORMACIÓN BRONZE → SILVER
# ============================================================

silver = cleaner.transform(pasajeros)

print("Pasajeros en Silver:", len(silver))


# ============================================================
# 5. TRANSFORMACIÓN SILVER → GOLD
# ============================================================

gold = builder.transform(silver)

print("Pasajeros en Gold:", len(gold))


# ============================================================
# 6. REALIZAR PREDICCIONES
# ============================================================

X = gold[FEATURES]

predicciones = modelo.predict(X)

print("Predicciones realizadas:", len(predicciones))


# ============================================================
# 7. PREPARAR RESULTADOS
# ============================================================

resultados = pd.DataFrame({
    "id": gold["id"].to_numpy(),
    "predicted_satisfaction": predicciones,
    "model_version": int(version.version)
})

print(resultados.head(10))


# ============================================================
# 8. GUARDAR PREDICCIONES EN POSTGRESQL
# ============================================================

db.write(
    resultados,
    "gold",
    "passenger_satisfaction_predictions"
)

print("Predicciones guardadas correctamente en PostgreSQL")