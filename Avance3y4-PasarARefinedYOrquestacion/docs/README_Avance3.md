# Proyecto Integrador – Avance 3  
## Procesamiento y Paso a Zona Refined

Este proyecto continúa el pipeline de datos climáticos, tomando los archivos originales de la **zona RAW del Data Lake** y procesándolos utilizando **Apache Spark**. Para coordinar la ejecución, se implementa orquestación remota con **Apache Airflow**.

El objetivo de este avance es unificar las mediciones de las distintas ciudades extraídas, limpiar y estructurar los datos y guardarlos en la **zona Refined** en formato columnar **Parquet** optimizado.

---

# Arquitectura del flujo de datos

El pipeline implementado en este avance sigue el siguiente flujo:

Amazon S3 (raw/historicos)  
↓  
Apache Spark (Procesamiento en EC2)  
↓  
Amazon S3 (refined/weather_unified_parquet)  
↑  
Apache Airflow (Orquestación en EC2)

Los archivos almacenados en múltiples particiones JSON (`.jsonl.gz`) se leen y transforman, para luego consolidarse en un único conjunto de datos limpio para analítica.

---

# 1. Configuración del Entorno, Usuarios y Permisos IAM

Para dotar a los servidores del acceso seguro a los servicios requeridos, se configura IAM en AWS.

1. Se crea un nuevo usuario en IAM con permisos para EC2 y generación de Access Key.
2. Se generan las credenciales y se configura la AWS CLI en PowerShell.
3. Se crea la clave SSH (`SparkKeyV3.pem`) y se ajustan sus permisos en Windows para asegurar la conexión segura a las instancias.

Para evitar el uso de credenciales *hardcodeadas* (claves explícitas en el código de Spark), se crea un **Rol IAM** asociado a un **Perfil de Instancia**:
- Se configura un archivo de políticas de confianza.
- Se le otorgan permisos de acceso completo a S3 (`AmazonS3FullAccess`).
- Este Perfil de Instancia se adjunta al nodo EC2 de Spark al momento de crearlo.

![Creación del Rol y Perfil](img/01-Usuario.png)

---

# 2. Lanzamiento de los Servidores (Spark y Airflow)

Se despliegan dos servidores independientes en AWS EC2, usando la imagen Amazon Linux 2023. Ambas máquinas se lanzan en instancias `t3.small` con 16 GB de almacenamiento EBS (gp3) para evitar posibles errores de disco durante el procesamiento.

- **Servidor 1: Spark Compute Node**
  - Ejecuta el motor de procesamiento distribuido.
  - Instancia: `t3.small`
  - Perfil IAM asociado para lectura/escritura en S3.

- **Servidor 2: Airflow Orchestrator**
  - Contiene el orquestador encargado de iniciar las tareas.
  - Instancia: `t3.small`

Una vez levantadas, se capturan las direcciones IP Públicas y Privadas necesarias para las conexiones SSH.

![Lanzamiento EC2](img/03-LanzamientoEC2.jpg)
![alt text](img/04-Lanzamiento.jpg)
![alt text](img/05-Lanzamiento.jpg)

---

# 3. Despliegue del Nodo Spark

Se establece una conexión SSH hacia el **Servidor 1** usando la clave PEM y la IP pública. 
![Obtener IP públicas](img/06-IPS.jpg)

En este entorno temporal se realiza la instalación del motor Docker y se genera una red aislada (`spark-net`). 
Posteriormente, se levantan dos contenedores para habilitar el cluster *standalone* de Spark:
- `spark-master` (Expone puerto 8080 de UI y 7077 de conexión)
- `spark-worker` (Con 2 cores y 2g de memoria)

### Generación del Script ETL Python (`etl_weather_s3.py`)

Se programa un script en PySpark para procesar la información. 
El script realiza las siguientes tareas:

1. Levanta la sesión y asigna los provider correctos de credenciales de Instancia (`InstanceProfileCredentialsProvider`)
2. Lee los archivos históricos JSON comprimidos (`.jsonl.gz`) directo desde las rutas S3 para los streams de `weather_patagonia` y `weather_riohacha`.
3. Extrae las variables de interés anidadas dentro de la estructura de OpenWeather (`_airbyte_data.current.*` y `_airbyte_data.*`):
   - `dt` (Timestamp)
   - `lat` (Latitud)
   - `lon` (Longitud)
   - `temp` (Temperatura)
   - `humidity` (Humedad)
4. Agrupa todos los registros usando una unión (Union) y asigna la literal `source_stream` indicando el origen de los datos.
5. Exporta el DataFrame final hacia la carpeta `refined/weather_unified_parquet` sobrescribiendo en formato **Parquet** con compresión Snappy.

El script se transfiere e inyecta al interior de la partición compartida del contenedor `spark-master` usando `docker cp`.

![Transferencia Script a Contenedor](img/07-ScriptAContenedor.jpg)
---

# 4. Despliegue del Nodo Airflow

Se establece una conexión SSH hacia el **Servidor 2**.

Al igual que en el nodo de procesamiento, se instala y configura Docker. A continuación, se lanza el contenedor de `apache/airflow` en modo `standalone`, asociándole un volumen local para la configuración de DAGs y definiendo un usuario administrador.

![Instalación Airflow](img/08-Airflow.jpg)

### Creación del Orquestador Remoto (DAG)
Se crea un archivo `spark_remote_etl.py`. Este DAG incluye un operador `SSHOperator` que permite a Airflow conectarse de forma remota al nodo de Spark y ejecutar explícitamente el binario de `spark-submit`. 

En la submit de Spark, se descargan primero dinámicamente los paquetes necesarios para AWS/Hadoop (`hadoop-aws` y `aws-java-sdk`), lo que posibilita a Spark interpretar los prefijos virtuales S3 y guardar la información procesada.

![Configuración DAG SSH](img/pegar-captura-operador-ssh)

---

# 5. Configuración de Conexión y Ejecución (Airflow UI)

Para permitir que el `SSHOperator` de Airflow ingrese al nodo de Spark, es necesario configurar una Conexión interna dentro de Airflow de tipo "SSH". 

Para inyectar la clave RSA de forma correcta en la interfaz, se procesa el archivo `.pem` original en la terminal de Windows transformando los saltos de línea y formateándolos en un objeto JSON compatible con el campo Extra de las credenciales de Airflow.

![Truco Json RSA](img/09-Parquets.jpg)

Finalmente, se accede a la interfaz gráfica web de Airflow en el puerto 8080 del Servidor 2, y en Admin -> Connections se guarda esta nueva conexión. 

Se procede a activar y realizar un Trigger del DAG `orquestador_remoto_spark`. Durante la ejecución, desde la propia UI de Airflow es posible verificar los logs transmitidos en tiempo real por el proceso remoto de Spark, que arrojará el éxito o error una vez que el Driver finalice y retorne el código de estado.

![Log Spark en Airflow](img/10-AiflowUI.jpg)

---

# Resultados y Estructura Actual del Data Lake

Tras la ejecución exitosa del pipeline de agregación vía DAG, las mediciones climáticas unificadas pueden validarse corriendo una instancia de `PySpark` interactivo, comprobando de este modo la creación de la particiones.

La estructura del Data Lake queda lista para el paso de visualización y Analytics:

`datalake-energy-dev-marianagil`  
│  
├── `raw/`  
│   ├── `ingesta-tiempo-real/`  
│   └── `historicos/` (JSON almacenados con Timestamp)  
│  
└── `refined/`  
    └── `weather_unified_parquet/` (DataFrames normalizados en formato Columnar Snappy.Parquet)  

![Comprobación Parquet Creados](img/pegar-captura-final-pyspark)

---

# Tecnologías utilizadas

- Apache Spark (PySpark)
- Apache Airflow
- Docker
- Amazon Web Services (EC2, IAM, S3)
- Python
- GitHub Actions (CI/CD)

---

# Proyecto Integrador – Avance 4
## Capa Analytics (Gold) y CI/CD

En este último avance unificado, expandimos el alcance del pipeline original para cumplir con los requerimientos analíticos y de integración continua pautados para el final del módulo.

### 1. Transformación hacia la Capa Gold (Analytics)
Se creó un nuevo script en PySpark (`etl_analytics.py`) encargado de consumir la capa Refined y responder a las preguntas de negocio estructurales. 
Dicho script incorpora la velocidad del viento (`wind_speed`) y la medición de nubosidad (`clouds`) agregadas previamente para formular heurísticas de:
- **Potencial Solar:** Calculado en horas diurnas (7-18hs), premiando altas temperaturas y penalizando altos índices de nubosidad.
- **Potencial Eólico:** Calculado linealmente a partir de la velocidad neta del viento originada en cada ciudad.

El resultado consolida la limpieza de fechas (`timestamp UNIX` a Fecha/Hora legible) y se almacena en el **Data Lake** (`analytics/energy_potential/`) particionado por ciudad en formato Parquet, exportando adicionalmente a un archivo unificado `.csv` para facilitar inspecciones del cliente.
![DatosCSV](img/11.2-DatosCSV.jpg)

### 2. Orquestación Secuencial en Airflow
El DAG `spark_remote_etl.py` fue modificado para invocar en cascada los procesos de procesamiento (Refined -> Analytics) usando `SSHOperator`. 
Adicionalmente, se deshabilitó la recopilación de logs en la base de datos de Airflow (`do_xcom_push=False`) con el fin de evitar desbordamientos de memoria RAM (*OOM / SIGTERM*) experimentados al orquestar desde instancias de nivel gratuito `t3.small` hacia servidores Spark de bajos recursos.

![DAG Completo Secuencial en Airflow UI](img/11-AirflowAnalytics.jpg)

### 3. Integración y Despliegue Continuo (CI/CD)
Se automatizó la actualización del código Python sobre la máquina EC2 albergando Spark a través de flujos en la nube mediante un pipeline de **GitHub Actions** (`deploy-spark.yml`):
1. **Event Trigger:** Se dispara ante cada `git push` a la rama `main` que detecte cambios en la capeta de `scripts/`.
2. **Setup Seguro:** Conexión estricta a través del grupo de seguridad de AWS empleando llaves inyectadas vía *GitHub Repository Secrets* (`EC2_HOST` y `EC2_SSH_KEY`). 
3. **Despliegue Interno:** Copiado recursivo del código fuente hacia el subsistema de Amazon Linux y posterior inyección en caliente dentro del volumen local del contenedor activo `spark-master` mediante `docker cp`.

![Ejecución Exitosa CI/CD en GitHub](img/12-CiCd.jpg)

### 4. Presentación y Dashboard Interactivo 
Para dar cierre al ciclo de Ingeniería de Datos y responder  a las **preguntas de negocio** planteadas en la consigna, se conectó localmente la Capa Gold consolidada (Archivos `.csv`) hacia un entorno de **Jupyter Notebook**.
Mediante los módulos de visualización (`pandas`, `matplotlib`, `seaborn`) se graficaron y calcularon las siguientes heurísticas derivadas del Data Lake:
- Curva de distribución promedio del Potencial Solar por franja horaria.
- Análisis de la estacionalidad diaria del Potencial Eólico (Velocidad de viento sostenida).
- Impacto negativo probabilístico de la nubosidad en la captación térmica.
- Fechas Históricas Pico (Mayor radiación en Patagonia y Riohacha / Menor propulsión eólica global).

El código fuente de los gráficos se encuentra adjunto en el documento `notebooks/Respuestas_Negocio.ipynb`.

![Visualización en Jupyter Notebook](img/13-PreguntasDeNegocio.jpg)
