# Energy Potential Data Lake (Lambda Architecture)

Bienvenido/a al repositorio oficial de arquitectura de datos para el ecosistema de **Monitoreo de Potencial Energético**. Este proyecto documenta el diseño, desarrollo y despliegue productivo de un Data Lake en la nube (AWS), implementando una **Arquitectura Lambda** para el procesamiento concurrente de datos históricos (Batch) y en tiempo real (Streaming) orientados a la industria meteorológica y de energías renovables.

El ciclo de vida del dato se encuentra modularizado en diferentes fases de ingeniería, asegurando escalabilidad, resiliencia y gobierno de la información a través de toda la tubería. Cada fase de la implementación cuenta con su respectiva documentación técnica.

---

## 🎯 Topología y Documentación del Proyecto

El despliegue de esta arquitectura de datos se dividió en hitos técnicos estratégicos. Para facilitar la lectura y el gobierno de la información, **cada fase (o avance de la cursada) contiene su propio documento técnico detallado (`README.md`) dentro de su respectiva subcarpeta `docs/`**. 

Puede explorar la documentación de implementación detallada y el código fuente de cada fase ingresando a los siguientes enlaces:

### 🚀 [Fase 1: Diseño Conceptual y Arquitectura en la Nube](./Avance1-DiseñoDeArquitectura/)
Definición estructural y modelado del ciclo de vida del dato.
*   **Alcance:** Establecimiento de la arquitectura fundacional. Comprende los diagramas de flujo de datos, la selección del *stack* tecnológico en AWS (EC2, S3) y la definición de las capas lógicas del Data Lake (Raw, Refined, Gold).

### 📥 [Fase 2: Motor de Ingesta (Airbyte & Data Lake AWS S3)](./Avance2-IngestaRaw/docs/)
Adquisición de datos estructurados desde APIs externas como *Source of Truth*.
*   **Alcance:** Aprovisionamiento de infraestructura Cloud (EC2) y despliegue local de conectores de **Airbyte**. Ingesta controlada de telemetría meteorológica (JSON) y consolidación en el almacenamiento escalable de la Capa Raw (S3 Data Lake).

### 🧹 [Fase 3: Procesamiento Batch (ETL), Orquestación y CI/CD](./Avance3y4-PasarARefinedYOrquestacion/docs/)
Estandarización de calidad de datos, despliegue de lógicas de negocio y automatización del linaje.
*   **Alcance:** 
    *   **Orquestación:** Implementación del scheduler **Apache Airflow** para ejecución cíclica y controlada de las pipelines.
    *   **Normalización Refined:** Trabajos de PySpark que ingieren la data cruda, ejecutan control de calidad (eliminación de nulos y duplicados) y estructuración tipada (Parquet).
    *   **Proyección Gold:** Motorización PySpark para cálculo agregado de Potencial Energético Eólico y Solar.
    *   **DevOps:** Diseño de flujos **CI/CD con GitHub Actions** garantizando despliegues automatizados entre el entorno de control de versiones y el clúster Spark.

### ⚡ [Fase 4: Procesamiento en Tiempo Real (Apache Kafka & Spark Streaming)](./Avance5-Kafka/docs/)
Implementación de la **Arquitectura Lambda** integral, permitiendo la confluencia de flujos persistentes con eventos en vivo.
*   **Alcance:** Inicialización de un clúster **Apache Kafka** vía Docker Compose. Creación de una capa de ingesta en sub-segundos a través de PySpark Structured Streaming. Los flujos Reactivos de Kafka interceptan los micropaquetes climáticos, los estructuran "on-the-fly" y los unifican (`unionByName`) contra la base Batch histórica, proveyendo al usuario analítico final de una vista Gold unificada, sin latencia informacional.

---
**Data Engineer:** Mariana Gil 
**Desarrollo Profesional:** Cohorte intensiva de Especialización Data Engineering
