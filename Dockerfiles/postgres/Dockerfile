FROM postgres:13

# Agregamos los files de las bases
COPY datasets/ /datasets/

# Script para iniciar los schemas medallion
COPY postgres/create_schemas.sql /docker-entrypoint-initdb.d/01_create_schemas.sql

