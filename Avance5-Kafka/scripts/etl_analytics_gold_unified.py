import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, round

def main():
    spark = SparkSession.builder \
        .appName("ETL_Analytics_Gold_Unified") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    bucket = "datalake-energy-dev-marianagil"
    
    # Rutas de entrada: Tomamos de AMBOS mundos (Batch viejo y Streaming nuevo)
    input_path_batch = f"s3a://{bucket}/refined/weather/"
    input_path_stream = f"s3a://{bucket}/processed-streaming/weather/"
    
    # Ruta de salida única (Capa GOLD)
    output_path = f"s3a://{bucket}/analytics/energy_potential_unified/"

    try:
        print(">>> Leyendo historial Batch (Refined)...")
        # El try/except interno es para que el código no explote si la carpeta de streaming aún no existe en S3
        # porque Spark a veces falla al leer carpetas vacías/inexistentes
        df_batch = spark.read.parquet(input_path_batch)
        
        try:
            print(">>> Leyendo datos recientes (Processed-Streaming)...")
            df_stream = spark.read.parquet(input_path_stream)
            
            # SI ambos existen, los pegamos uno abajo del otro con unionByName
            print(">>> Unificando Batch y Streaming...")
            df_unified = df_batch.unionByName(df_stream, allowMissingColumns=True)
        except Exception:
            print(">>> No se encontraron datos de streaming o la carpeta no existe aún. Usando solo Batch.")
            df_unified = df_batch
        
        print(">>> Calculando lógicas de negocio (Potencial Solar y Eólico)...")
        
        # Exactamente la misma lógica matemática que tenías en Avance 4 para calcular Potencial
        df_potencial_solar = df_unified.withColumn("potencial_solar", 
                                            when((col("hora") >= 7) & (col("hora") <= 18),
                                                 round((col("temp") * 0.8) - (col("clouds") * 0.2), 2))
                                            .otherwise(0.0))
        
        df_final = df_potencial_solar.withColumn("potencial_eolico", 
                                               round(col("wind_speed") * 10, 2))
        
        print(">>> Guardando Capa GOLD final (Batch + Streaming)...")
        # Esto NO ES STREAMING, es un proceso BATCH normal que se ejecutará en Airflow,
        # así que usamos el 'write' común de siempre.
        df_final.write.mode("overwrite").partitionBy("source_stream").parquet(output_path)
        
        print(">>> ETL Gold Unificado finalizado exitosamente.")
        
    except Exception as e:
        print(f"ERROR GENERAL: {str(e)}")
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
