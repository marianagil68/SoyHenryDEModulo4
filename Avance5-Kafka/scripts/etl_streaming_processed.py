import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_unixtime, to_date, hour, month

def main():
    # 1. Creamos la sesión de Spark para el procesamiento secundario
    spark = SparkSession.builder \
        .appName("ETL_Weather_Streaming_PROCESSED") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")

    bucket = "datalake-energy-dev-marianagil"
    
    input_path = f"s3a://{bucket}/raw-streaming/weather/"
    output_path = f"s3a://{bucket}/processed-streaming/weather/"
    
    checkpoint_path = f"s3a://{bucket}/checkpoints/processed-streaming/"

    print(">>> Iniciando procesamiento desde S3 Raw-Streaming...")

    try:
        # 2. Leemos en streaming, pero esta vez desde una carpeta de S3 (Archivos Parquet)
        # Spark se da cuenta solo cuando aparece un archivo nuevo gracias a su schema
        df_raw_stream = spark.readStream \
            .format("parquet") \
            .option("path", input_path) \
            .schema('dt long, lat double, lon double, temp double, humidity int, wind_speed double, clouds int, source_stream string') \
            .load()

        # 3. Aplicamos transformaciones
        # Convertimos la fecha UNIX a columnas más fáciles de leer (Día, hora, mes)
        df_transformed = df_raw_stream \
            .withColumn("timestamp_str", from_unixtime(col("dt"))) \
            .withColumn("fecha_dia", to_date(col("timestamp_str"))) \
            .withColumn("hora", hour(col("timestamp_str"))) \
            .withColumn("mes", month(col("timestamp_str")))

        print(">>> Iniciando escritura continua hacia S3 (Capa Processed-Streaming)...")

        # 4. Escribimos en S3 a la carpeta processed-streaming
        query = df_transformed.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", checkpoint_path) \
            .partitionBy("source_stream") \
            .start()

        # Lo dejamos corriendo
        query.awaitTermination()

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
