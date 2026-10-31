FROM postgres:13

# Variables de entorno
ENV POSTGRES_DB=mlops_ceia
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

COPY create_schemas.sql create_table.sql  /docker-entrypoint-initdb.d/