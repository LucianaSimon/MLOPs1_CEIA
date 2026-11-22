FROM postgres:13

# Agregamos los files de las bases
COPY datasets/ /datasets/

# Base de MLflow, separada de las tablas de pasajeros
COPY postgres/create_mlflow_db.sql /docker-entrypoint-initdb.d/00_create_mlflow_db.sql

# Script para iniciar los schemas medallion
COPY postgres/create_schemas.sql /docker-entrypoint-initdb.d/01_create_schemas.sql

