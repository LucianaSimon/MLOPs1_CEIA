# MLOps I — Arquitectura reproducible para satisfacción de pasajeros

Especialización en Inteligencia Artificial — CEIA, Universidad de Buenos Aires
Trabajo práctico grupal | Documentación de arquitectura, implementación y operación

> Enfoque de la entrega. El objetivo central es demostrar cómo se implementó un sistema de MLOps: separación de responsabilidades, persistencia, transformación de datos, entrenamiento, registro de modelos, inferencia, contenerización y reproducibilidad. La calidad predictiva del clasificador no es el criterio principal de este documento.

## Integrantes

1. Matias Souto
2. Luciana Simón González
3. Franco Solano Lombardi
4. Bernardo Eppenstein

## 1. Resumen de la solución

Se implementó una arquitectura local de MLOps para un caso de clasificación binaria de satisfacción de pasajeros. El problema predictivo sirve como vehículo para demostrar un ciclo técnico completo: datos de origen → almacenamiento → transformación → entrenamiento → registro versionado → inferencia → persistencia de resultados.

Los componentes principales son:

| Componente | Tecnología | Responsabilidad |
| --- | --- | --- |
| Almacenamiento de datos | PostgreSQL | Tablas de entrada, capas Bronze/Silver/Gold y resultados de inferencia |
| Procesamiento y entrenamiento | Python, pandas, scikit-learn | Transformaciones, entrenamiento y evaluación |
| Seguimiento y registro | MLflow | Experimentos, parámetros, métricas, artefactos y versiones del modelo |
| Almacenamiento de objetos | MinIO (compatible con S3) | Bucket `data` disponible en la infraestructura; todavía no integrado al flujo de entrenamiento ni a MLflow |
| Ejecución aislada | Docker | Empaquetado de dependencias y procesos |
| Coordinación de servicios | Docker Compose | Construcción, redes, variables de entorno, dependencias y volúmenes |
| Versionado e integración | Git y GitHub | Ramas de trabajo, commits y Pull Requests |

La principal decisión de diseño es desacoplar el entrenamiento de la inferencia. El proceso de predicción no vuelve a entrenar: recupera un modelo registrado y los transformadores correspondientes a la misma corrida.

## 2. Arquitectura general

### 2.1 Dos flujos con responsabilidades diferentes

Entrenamiento: PostgreSQL Bronze → DataCleaner.fit/transform → Silver → FeatureBuilder.transform → Gold → SatisfactionClassifier → MLflow Registry y artefactos.

Inferencia: PostgreSQL Bronze (nuevos pasajeros) → DataCleaner.transform ya ajustado → FeatureBuilder.transform → modelo recuperado de MLflow → PostgreSQL Gold (predicciones).

Esta separación evita que el proceso de inferencia dependa de ejecutar nuevamente la etapa de entrenamiento. También hace explícita la trazabilidad: cada predicción incluye model_version.

## 3. Docker Compose: servicios e infraestructura

La arquitectura definida en docker-compose.yml contempla seis servicios: los cuatro del flujo de MLOps (postgres, mlflow, trainer y prediction) y dos de almacenamiento de objetos (s3 y create_s3_buckets).

| Servicio | Imagen / construcción | Dependencias | Persistencia / salida |
| --- | --- | --- | --- |
| postgres | Dockerfiles/postgres/Dockerfile | Ninguna | Volumen db_data; puerto 5432 |
| mlflow | Dockerfiles/mlflow/Dockerfile | PostgreSQL saludable | Volumen mlflow_data; puerto 5000 |
| trainer | Dockerfiles/trainer/Dockerfile | PostgreSQL y MLflow saludables | Carpeta local ./artifacts montada en /artifacts |
| prediction | Dockerfiles/prediction/Dockerfile | PostgreSQL y MLflow saludables | Escribe resultados en PostgreSQL |
| s3 | Imagen coollabsio/minio | Ninguna | Puertos 9000 (API) y 9001 (consola); red backend |
| create_s3_buckets | Imagen coollabsio/minio | Servicio s3 | Crea el bucket `data` al iniciar y finaliza |

### 3.1 Redes y estado de MinIO

El archivo define una red `backend` (tipo bridge), utilizada por los servicios de MinIO. Los servicios postgres, mlflow, trainer y prediction se comunican entre sí por la red por defecto de Compose.

MinIO se incorporó a la infraestructura mediante el Pull Request #2, pero por ahora no forma parte del flujo de datos: MLflow guarda sus artefactos en el volumen mlflow_data y el pipeline no escribe en el bucket. Integrarlos (por ejemplo, usar el bucket como destino de artefactos de MLflow) queda como mejora futura. El servicio s3 no tiene volumen configurado, por lo que su contenido no persiste si el contenedor se recrea.

## 4. PostgreSQL y arquitectura Medallion

La base principal es mlops_ceia; MLflow utiliza además mlflow_db para su backend de tracking. Los scripts de inicialización están en Dockerfiles/postgres/.

| Capa | Función | Ejemplos |
| --- | --- | --- |
| Bronze | Conservar registros de origen | bronze.passenger_satisfaction_train, bronze.passenger_satisfaction_test |
| Silver | Guardar datos luego de limpieza y normalización | silver.passenger_satisfaction_train, silver.passenger_satisfaction_test |
| Gold | Guardar características para modelado y salidas | gold.passenger_satisfaction_train, gold.passenger_satisfaction_test, gold.passenger_satisfaction_predictions |

Los CSV se encuentran en Dockerfiles/datasets/train.csv y Dockerfiles/datasets/test.csv. El script de inicialización de PostgreSQL crea esquemas/tablas y carga datos a Bronze. Los archivos contienen 103.904 registros de entrenamiento y 25.976 de test, respectivamente.

### 4.1 Transformaciones

pipeline/cleaning.py implementa DataCleaner, encargado de la limpieza y del tratamiento de datos faltantes. Se ejecuta fit solamente con entrenamiento y luego transform tanto sobre entrenamiento como sobre test; así se reutilizan las reglas aprendidas y se evita calcularlas con datos de evaluación.

pipeline/features.py implementa FeatureBuilder, que construye y selecciona las características esperadas por el modelo. El procesamiento admite datos sin la variable objetivo satisfaction durante la inferencia, mientras que el entrenamiento necesita esa variable.

### 4.2 Comportamiento de escritura

pipeline/database.py encapsula la lectura/escritura SQL. Su método write utiliza reemplazo de tabla (if_exists="replace"). Por lo tanto, las tablas de salida se regeneran en cada ejecución: no existe todavía un mecanismo de actualización incremental ni de conservación histórica de predicciones.

## 5. Pipeline de entrenamiento

El punto de entrada es python -m pipeline.run, ejecutado por el servicio trainer.

El orquestador de aplicación es la clase MedallionPipeline en pipeline/run.py. Su método run() realiza, en este orden:

1. Lee train y test desde Bronze, ordenados por raw_id.
2. Ajusta DataCleaner exclusivamente con train.
3. Transforma ambos conjuntos y los escribe en Silver.
4. Construye las características y escribe ambos conjuntos en Gold.
5. Ejecuta validación cruzada sobre el conjunto de entrenamiento.
6. Entrena el clasificador y evalúa sobre test.
7. Guarda model.joblib y metrics.json.
8. Si está configurado MLFLOW_TRACKING_URI, registra la corrida y publica el modelo en MLflow.

### 5.1 ¿Qué se guarda y por qué?

- model.joblib: un paquete con cleaner, builder y classifier, necesario para aplicar exactamente las transformaciones ajustadas durante el entrenamiento.
- metrics.json: evidencia de la ejecución y evaluación; se conserva por trazabilidad, no porque la nota del trabajo dependa de obtener una métrica alta.
- Modelo MLflow: el pipeline de scikit-learn se registra bajo el nombre passenger_satisfaction.

El clasificador implementado es Random Forest. Su elección es secundaria frente al diseño del flujo: el foco está en la capacidad de entrenar, registrar y reutilizar un modelo de manera consistente.

## 6. MLflow: tracking, artefactos y registro de modelos

MLflow cumple dos funciones complementarias:

Tracking: registra la ejecución del entrenamiento, sus parámetros, métricas y artefactos. pipeline/run.py crea o selecciona el experimento passenger_satisfaction y abre una corrida con mlflow.start_run().

Model Registry: publica el modelo con registered_model_name="passenger_satisfaction". El registro permite referirse a versiones concretas del modelo en lugar de depender de un archivo local sin identificación.

### 6.1 Consistencia entre modelo y preprocesamiento

En el módulo de inferencia probado, la versión del modelo se obtiene mediante MlflowClient. A partir del run_id asociado se descarga model.joblib, que contiene los transformadores usados en esa misma corrida. Así se evita combinar accidentalmente un modelo con transformaciones ajustadas en otro entrenamiento.

## 7. Inferencia desacoplada: servicio prediction

El módulo predictions.py implementa inferencia por lotes sin volver a ajustar transformadores ni entrenar el clasificador.

Secuencia implementada y probada:

1. Conecta a MLflow mediante MLFLOW_TRACKING_URI.
2. Recupera models:/passenger_satisfaction/1.
3. Identifica el run_id de esa versión y descarga model.joblib de la misma corrida.
4. Lee los registros de bronze.passenger_satisfaction_predict.
5. Aplica cleaner.transform() y builder.transform().
6. Selecciona las columnas definidas en FEATURES.
7. Ejecuta modelo.predict(X).
8. Escribe id, predicted_satisfaction y model_version en gold.passenger_satisfaction_predictions.

Prueba realizada: se ejecutó el contenedor prediction con 100 pasajeros y se almacenaron 100 resultados en PostgreSQL.

### 7.1 Preparación de datos sin etiqueta

El proyecto incluye scripts/create_prediction_data.sql, que crea bronze.passenger_satisfaction_predict a partir de 100 filas de bronze.passenger_satisfaction_test y elimina satisfaction.

Esto es un mecanismo de prueba, no una ingesta de pasajeros reales. Requiere que la tabla de test ya exista. El script usa CREATE TABLE IF NOT EXISTS, por lo que no duplica registros si la tabla ya fue creada.

## 8. Reproducción de la arquitectura desde cero

### 8.1 Requisitos

- Docker Desktop con Docker Compose disponible.
- Git para obtener el repositorio.
- Puertos locales 5432 (PostgreSQL), 5000 (MLflow), 9000 y 9001 (MinIO) disponibles, o adaptar el mapeo.
- La versión integrada del repositorio (rama main) con el servicio prediction para ejecutar inferencia.

> Advertencia: los siguientes comandos asumen que los scripts de inicialización se ejecutan sobre un volumen PostgreSQL nuevo. Si ya existe db_data, los scripts de inicialización no necesariamente se vuelven a ejecutar.

### 8.2 Obtener el proyecto y levantar infraestructura

```bash
git clone https://github.com/LucianaSimon/MLOPs1_CEIA.git
cd MLOPs1_CEIA

# Levantar base de datos y servidor MLflow
docker compose up -d --build postgres mlflow

# Verificar estado
docker compose ps
```

La interfaz MLflow estará disponible localmente en el puerto 5000. En la primera inicialización, PostgreSQL prepara las bases, los esquemas y los datos incluidos en los CSV.

Opcionalmente, para levantar también MinIO y crear el bucket `data`:

```bash
docker compose up -d s3 create_s3_buckets
```

La consola web de MinIO queda disponible en el puerto 9001 (usuario `minio`, contraseña `minio123`, definidos en docker-compose.yml).

### 8.3 Entrenar y registrar el modelo

```bash
docker compose build trainer
docker compose run --rm trainer
```

Este paso es necesario en un entorno nuevo para disponer de un modelo registrado y sus artefactos en MLflow. La ejecución también produce artifacts/model.joblib y artifacts/metrics.json en la carpeta local montada.

### 8.4 Crear pasajeros de prueba

Windows / Anaconda Prompt (CMD):

```bash
docker compose exec -T postgres psql -U postgres -d mlops_ceia < scripts\create_prediction_data.sql
```

Linux / macOS / shell compatible:

```bash
docker compose exec -T postgres psql -U postgres -d mlops_ceia < scripts/create_prediction_data.sql
```

Nota: el script fue probado con una base que ya contenía los datos de test. Si la tabla de origen no existe, debe resolverse primero la carga de Bronze.

### 8.5 Ejecutar inferencia

```bash
docker compose build prediction
docker compose run --rm prediction
```

En el entorno de desarrollo se comprobó también la ejecución con --no-deps cuando PostgreSQL y MLflow ya estaban levantados:

```bash
docker compose run --rm --no-deps prediction
```

### 8.6 Verificar resultados

```bash
docker compose exec postgres psql -U postgres -d mlops_ceia -c "SELECT COUNT(*) FROM bronze.passenger_satisfaction_predict;"

docker compose exec postgres psql -U postgres -d mlops_ceia -c "SELECT id, predicted_satisfaction, model_version FROM gold.passenger_satisfaction_predictions LIMIT 10;"
```

El primer conteo debería ser 100 después de preparar los datos de prueba. El segundo comando debe devolver filas solamente después de ejecutar la inferencia correctamente.

## 9. Organización del repositorio

```text
MLOPs1_CEIA/
├── README.md                        # Documentación del proyecto
├── docker-compose.yml               # Infraestructura y servicios
├── .dockerignore                    # Contexto de construcción de imágenes
├── Dockerfiles/
│   ├── datasets/
│   │   ├── train.csv
│   │   └── test.csv
│   ├── postgres/
│   │   ├── Dockerfile
│   │   ├── create_schemas.sql
│   │   └── create_mlflow_db.sql
│   ├── mlflow/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── trainer/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── airflow/
│   │   └── download_kaggle.py       # Utilidad auxiliar, no DAG activo
│   └── prediction/                  # Servicio de inferencia
│       ├── Dockerfile
│       └── requirements.txt
├── pipeline/
│   ├── config.py                    # Definiciones de columnas y variables
│   ├── database.py                  # Acceso a PostgreSQL
│   ├── cleaning.py                  # Limpieza y ajuste de imputación
│   ├── features.py                  # Ingeniería de características
│   ├── training.py                  # Clasificador y evaluación
│   └── run.py                       # Pipeline de entrenamiento
├── predictions.py                   # Inferencia
├── scripts/
│   └── create_prediction_data.sql   # Datos de prueba
└── artifacts/                       # Se genera al ejecutar trainer
```

La estructura mezcla infraestructura (Dockerfiles, Compose), lógica de dominio (pipeline) y puntos de entrada (pipeline.run, predictions.py). Esto permite construir imágenes separadas para entrenamiento e inferencia.

## 10. Pruebas y criterios de aceptación de la arquitectura

La evaluación de esta entrega se enfoca en la ejecución técnica y en la trazabilidad, no en alcanzar un valor objetivo de accuracy o F1.

| Comprobación | Evidencia esperada |
| --- | --- |
| Infraestructura | docker compose ps muestra PostgreSQL y MLflow saludables |
| Inicialización | Existen esquemas Bronze, Silver y Gold y las tablas de origen |
| Entrenamiento | trainer finaliza y genera artefactos locales |
| Registro | MLflow muestra una corrida y una versión del modelo passenger_satisfaction |
| Consistencia | El paquete de transformadores corresponde al run_id de la versión utilizada |
| Datos de prueba | La tabla de inferencia contiene 100 pasajeros sin satisfaction |
| Inferencia | prediction procesa esos registros sin reentrenar |
| Persistencia | La tabla Gold de predicciones incluye id, resultado y versión |
| Portabilidad | Los servicios pueden construirse en otro equipo con Docker y datos/modelo inicializados |

## 11. Decisiones arquitectónicas y justificación

| Decisión | Beneficio | Contrapartida actual |
| --- | --- | --- |
| PostgreSQL como repositorio central | Persistencia y consultas SQL verificables | Requiere inicialización y gestión de esquemas |
| Bronze/Silver/Gold | Separa origen, limpieza y características | Escritura por reemplazo, no incremental |
| fit solo con train | Consistencia y menor riesgo de fuga de datos | Obliga a conservar el estado de transformadores |
| MLflow Registry | Versionado y trazabilidad del modelo | Registro local no compartido automáticamente |
| Docker por proceso | Aislamiento de dependencias y portabilidad | Se deben construir imágenes y configurar servicios |
| Inferencia independiente | No necesita volver a entrenar | Requiere modelo y artefactos previamente disponibles |
| SQL de datos de prueba | Permite demostrar el flujo sin fuente externa nueva | Depende de Bronze Test ya cargado |
| MinIO (compatible con S3) | Deja lista la base para almacenamiento de objetos y artefactos | Aún no integrado con MLflow ni con el pipeline; sin volumen persistente |
| Git con flujo feature → staging → main | Revisión y control de integración mediante Pull Requests | La integración depende de revisión y aprobación |