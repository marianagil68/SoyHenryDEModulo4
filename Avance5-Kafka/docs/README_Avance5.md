# Proyecto Integrador 4 - Data Engineering
## Avance 5: Implementación de Arquitectura Lambda (Batch + Streaming)

En este quinto avance del proyecto, se ha evolucionado la arquitectura de datos existente (orientada a procesos Batch vía Airflow) hacia una **Arquitectura Lambda** completa, incorporando capacidades de ingesta y procesamiento en tiempo real (Streaming) mediante Apache Kafka y Apache Spark Structured Streaming.

### Objetivos Alcanzados

1.  **Despliegue de Infraestructura de Streaming**:
    *   Se implementó Apache Kafka como broker de mensajería (junto con Zookeeper) conteneirizado mediante Docker Compose en la instancia EC2 principal.
    *   Se configuraron listeners remotos (`KAFKA_ADVERTISED_LISTENERS`) y políticas de red en AWS (Security Groups) para habilitar el tráfico TCP en el puerto 9092.

2.  **Capa Raw-Streaming (`etl_streaming_raw.py`)**:
    *   Se desarrolló un trabajo activo en **PySpark Structured Streaming** que se suscribe al tópico `weather_stream` de Kafka.
    *   Ingesta eventos JSON de clima en tiempo real, parsea su contenido y escribe continuamente bloques de datos en formato Parquet hacia la ruta `s3a://datalake-energy-dev-marianagil/raw-streaming/weather/`.

3.  **Capa Processed-Streaming (`etl_streaming_processed.py`)**:
    *   Se implementó un segundo trabajo de Spark Streaming que lee las actualizaciones de la capa Raw, aplica transformaciones de limpieza (casteo de tipos) y guarda el esquema estandarizado en la ruta `s3a://datalake-energy-dev-marianagil/processed-streaming/weather/`.

4.  **Capa Analítica Gold Unificada (`etl_analytics_gold_unified.py`)**:
    *   Se reescribió el proceso analítico final para que consuma en paralelo ambas fuentes de datos: el histórico **Batch** (Refined Layer) y el tiempo real **Streaming** (Processed-Streaming Layer).
    *   Utilizando operaciones `unionByName`, se consolidan ambos DataFrames y se calculan las métricas de negocio (`potencial_solar` acotado por hora diurna calculada desde timestamp unix, y `potencial_eolico`).
    *   El dataset unificado se sobrescribe en la ruta final `analytics/energy_potential_unified/` preparado para consumo visual o Machine Learning.

5.  **Pruebas de Ingesta**:
    *   Se diseñó el productor Python `test_kafka_producer.py` simulando telemetría meteorológica para inyectar datos reales al sistema y validar la correcta funcionalidad de la tubería continua desde Kafka $\rightarrow$ EC2 Spark $\rightarrow$ S3 Data Lake.

### Estructura de Scripts
*   `docker-compose.yml`: Archivo de orquestación local para levantar el ecosistema Kafka.
*   `test_kafka_producer.py`: Herramienta de testeo manual / productor Kafka.
*   `scripts/etl_streaming_raw.py`: PySpark Structured Streaming (Ingesta cruda).
*   `scripts/etl_streaming_processed.py`: PySpark Structured Streaming (Limpieza).
*   `scripts/etl_analytics_gold_unified.py`: Job PySpark Batch (Consolidación Lambda e indicadores matemáticos).
