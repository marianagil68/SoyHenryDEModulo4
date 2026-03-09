# Proyecto Integrador 4 - Data Engineering (SoyHenry)

Bienvenido/a al repositorio que documenta el desarrollo completo del **Proyecto Integrador 4** de Data Engineering de Mariana Gil. El objetivo general de este proyecto fue diseñar, desarrollar y desplegar en la nube (AWS) un Data Lake con ingesta continua (Lambda Architecture) orientado a la industria meteorológica y energética, partiendo desde cero.

Este repositorio se encuentra estructurado en módulos, los cuales reflejan el progreso iterativo e incremental a lo largo de las semanas cursadas (**Avances**). Cada carpeta documenta las fuentes de datos, los flujos, automatizaciones y configuraciones necesarias para cumplir los requerimientos solicitados.

---

## 🎯 Estructura del Repositorio

Para facilitar la lectura y corrección, cada Avance contiene su propio documento técnico detallado (`README.md`) dentro de su respectiva subcarpeta `docs/`. A continuación, un resumen de la evolución del proyecto:

### 🚀 [Avance 1: Diseño de Arquitectura](./Avance1-DiseñoDeArquitectura/)
Este fue el punto fundacional del proyecto. Se desarrolló la planificación estratégica y visual completa. 
*   **Qué incluye:** Diagramas UML/Flowcharts conceptuales detallando cómo viajarán los datos desde la API externa de origen (OpenWeather), pasando por herramientas de ingesta (Airbyte), almacenamiento en crudo en un Datalake (AWS S3) y eventual procesamiento transformacional mediante Spark hasta llegar al usuario de analíticas final.

### 📥 [Avance 2: Ingesta Raw (Airbyte & S3)](./Avance2-IngestaRaw/docs/)
Ejecución del acople con las fuentes de datos maestras para la construcción de la **Capa Cruda (Raw)**.
*   **Qué incluye:** Despliegue de un servidor EC2 en Amazon AWS, instalación local por CLI de la plataforma **Airbyte**, y configuración de los source connectors hacia la API de clima y destino hacia nuestro Data Lake remoto (Amazon S3). El resultado son los datos JSON históricos respaldados correctamente en la nube.

### 🧹 [Avances 3 y 4: Tranformación, Orquestación y Capa Gold](./Avance3y4-PasarARefinedYOrquestacion/docs/)
En este módulo se concentró el grueso del procesamiento por lotes matemáticos (Batch Data Processing).
*   **Qué incluye:** 
    *   **Airflow:** Instalación y configuración de Apache Airflow sobre el EC2. Creación del DAG para orquestar la recurrencia de la ingesta de Airbyte.
    *   **Spark Refined:** Script de PySpark para conectar a la capa Raw (JSON) de S3, limpiar nulos, deduplicar, establecer esquemas rígidos y guardar los datos pulidos en parquet bajo la Capa Refined.
    *   **Capa Analítica y GitHub Actions:** PySpark asume la capa **Gold** (Analytics) implementando las reglas de cálculo de Potencial Energético Eólico/Solar. Se instauró además una canalización de despliegue continuo (CI/CD) empleando GitHub Actions para automatizar lanzamientos de scripts hacia el servidor Spark sin conexión manual.

### ⚡ [Avance 5: Arquitectura Lambda y Streaming con Kafka](./Avance5-Kafka/docs/)
La cúspide técnica del pipeline: Transición desde lotes congelados hacia una autopista de datos en la nube que muta en tiempo real.
*   **Qué incluye:** Implementación completa de un clúster *Apache Kafka* + Zookeeper. Producción artificial de eventos instantáneos. PySpark *Structured Streaming* toma el mando con scripts `readStream`/`writeStream` para la ingesta reactiva y limpieza al vuelo de los micro-eventos producidos. Finalmente, la alteración del pipeline analítico `Avance 4` para permitir la amalgamación (`unionByName`) de los históricos con el streaming continuo, ofreciendo una lectura Gold única, coherente e inmediata.

---
**Autora:** Mariana Gil 
**Bootcamp:** Programa intensivo de Data Engineering - *[SoyHenry]*
