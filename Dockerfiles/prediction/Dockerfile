FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias
COPY Dockerfiles/prediction/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY pipeline/ pipeline/

# Copiar nuestro módulo de predicciones
COPY predictions.py .

# Ejecutar predicciones
CMD ["python", "predictions.py"]