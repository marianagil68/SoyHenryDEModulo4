import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_unixtime, to_date, hour, month, when, round
def main():
    spark = SparkSession.builder \
        .appName("ETL_Analytics_Gold") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    try:
        bucket = "datalake-energy-dev-marianagil"
        input_path = f"s3a://{bucket}/refined/weather/"
        
        print(">>> Leyendo capa Refined actualizada...")
        df_refined = spark.read.parquet(input_path)
        print(">>> Transformando a Analytics (Agregación de Potencial)...")
        
        # 1. Convertir timestamp UNIX a formatos legibles y extraer hora/mes
        df_dates = df_refined.withColumn("timestamp_str", from_unixtime(col("dt"))) \
                             .withColumn("fecha_dia", to_date(col("timestamp_str"))) \
                             .withColumn("hora", hour(col("timestamp_str"))) \
                             .withColumn("mes", month(col("timestamp_str")))
                             
        # 2. Algoritmos de estimación mejorados con nuevas variables
        # POTENCIAL SOLAR: Penaliza nubosidad alta (nubes % / 10). Premia temperaturas altas.
        # Solo válido de día (7 a 18 hs).
        df_potencial = df_dates.withColumn("potencial_solar", 
                                            when((col("hora") >= 7) & (col("hora") <= 18),
                                                 round((col("temp") * 0.8) - (col("clouds") * 0.2), 2))
                                            .otherwise(0.0))
        
        # POTENCIAL EÓLICO: Basado 100% en la velocidad del viento traída en Refined.
        # Suponemos un factor de conversión base de multiplicador x 10.
        df_analytics = df_potencial.withColumn("potencial_eolico", 
                                               round(col("wind_speed") * 10, 2))
        # 3. Guardado en Capa Gold / Analytics particionada por Ciudad
        output_path = f"s3a://{bucket}/analytics/energy_potential/"
        
        print(">>> Escribiendo Capa Gold en Parquet...")
        df_analytics.write.mode("overwrite").partitionBy("source_stream").parquet(output_path)
        
        # Guardado extra en CSV para revisión manual (1 solo archivo)
        csv_output_path = f"s3a://{bucket}/analytics/energy_potential_csv/"
        print(">>> Escribiendo copia en CSV para revisión...")
        df_analytics.coalesce(1).write.mode("overwrite").option("header", "true").csv(csv_output_path)
        
        print(">>> ETL Analytics finalizado exitosamente.")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
    finally:
        spark.stop()
if __name__ == "__main__":
    main()

# Prueba de CI CD para el Avance 4.