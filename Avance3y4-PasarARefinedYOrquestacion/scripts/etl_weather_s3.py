from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit
spark = SparkSession.builder \
    .appName("ETL_Weather_Normalization") \
    .getOrCreate()
print(">>> Extrayendo S3.")
bucket = "datalake-energy-dev-marianagil"
path_patagonia = f"s3a://{bucket}/raw/historicos/weather_patagonia/"
path_riohacha = f"s3a://{bucket}/raw/historicos/weather_riohacha/"
df_patagonia = spark.read.json(path_patagonia)
df_riohacha = spark.read.json(path_riohacha)
df_patagonia_norm = df_patagonia.select(
    col("_airbyte_data.dt").cast("long").alias("dt"),
    col("_airbyte_data.coord.lat").cast("double").alias("lat"),
    col("_airbyte_data.coord.lon").cast("double").alias("lon"),
    col("_airbyte_data.main.temp").cast("double").alias("temp"),
    col("_airbyte_data.main.humidity").cast("int").alias("humidity"),
    col("_airbyte_data.wind.speed").cast("double").alias("wind_speed"),
    col("_airbyte_data.clouds.all").cast("int").alias("clouds"),
    lit("weather_patagonia").alias("source_stream")
)
df_riohacha_norm = df_riohacha.select(
    col("_airbyte_data.dt").cast("long").alias("dt"),
    col("_airbyte_data.coord.lat").cast("double").alias("lat"),
    col("_airbyte_data.coord.lon").cast("double").alias("lon"),
    col("_airbyte_data.main.temp").cast("double").alias("temp"),
    col("_airbyte_data.main.humidity").cast("int").alias("humidity"),
    col("_airbyte_data.wind.speed").cast("double").alias("wind_speed"),
    col("_airbyte_data.clouds.all").cast("int").alias("clouds"),
    lit("weather_riohacha").alias("source_stream")
)
df_final = df_patagonia_norm.unionByName(df_riohacha_norm)
print(">>> Escribiendo capa REFINED.")
output_path = f"s3a://{bucket}/refined/weather/"
df_final.write.mode("overwrite").parquet(output_path)
print(">>> ETL FINALIZADO.")
spark.stop()