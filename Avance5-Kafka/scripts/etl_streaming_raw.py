import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, LongType

def main():
    # 1. Creamos la sesión de Spark. A diferencia de un batch, acá lo llamamos "Streaming_RAW"
    spark = SparkSession.builder \
        .appName("ETL_Weather_Streaming_RAW") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")

    KAFKA_BOOTSTRAP_SERVERS = "44.220.43.207:9092"
    KAFKA_TOPIC = "weather_stream"
    
    bucket = "datalake-energy-dev-marianagil"
    output_path = f"s3a://{bucket}/raw-streaming/weather/"
    checkpoint_path = f"s3a://{bucket}/checkpoints/raw-streaming/"

    print(">>> Iniciando lectura desde Kafka en STREAMING...")

    try:
        df_kafka = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("subscribe", KAFKA_TOPIC) \
            .option("startingOffsets", "earliest") \
            .load()

        # Los mensajes de Kafka llegan crudos en formato Bytes. Los pasamos a String (Texto).
        df_string = df_kafka.selectExpr("CAST(value AS STRING) as json_payload")

        # 3. Le decimos a Spark cómo es la "forma" de los datos que van a llegar adentro del JSON
        schema_clima = StructType([
            StructField("dt", LongType()),
            StructField("lat", DoubleType()),
            StructField("lon", DoubleType()),
            StructField("temp", DoubleType()),
            StructField("humidity", IntegerType()),
            StructField("wind_speed", DoubleType()),
            StructField("clouds", IntegerType()),
            StructField("source_stream", StringType())
        ])

        # 4. Usamos from_json para desenpaquetar el texto usando el esquema que armamos arriba
        df_parsed = df_string.withColumn("data", from_json(col("json_payload"), schema_clima)).select("data.*")

        print(">>> Iniciando escritura continua hacia S3 (Capa Raw-Streaming)...")

        # 5. Volvemos a usar la magia de Streaming: writeStream en lugar de write
        # Le decimos que lo guarde en Parquet y que vaya agregando archivos a medida que lleguen (append)
        query = df_parsed.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", checkpoint_path) \
            .start()

        # Esto deja el programa corriendo indefinidamente escuchando a Kafka
        query.awaitTermination()

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
