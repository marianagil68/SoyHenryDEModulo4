import json
import time
from kafka import KafkaProducer

try:
    print(">>> Conectando con Kafka en Airflow (44.220.43.207:9092)...")
    producer = KafkaProducer(
        bootstrap_servers=['44.220.43.207:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    dato_falso = {
        "_airbyte_data": {
            "dt": int(time.time()),
            "coord": {"lat": -43.25, "lon": -65.3},
            "main": {"temp": 15.5, "humidity": 60},
            "wind": {"speed": 22.4},
            "clouds": {"all": 10},
            "source_stream": "weather_patagonia"
        }
    }

    print(">>> Enviando un dato de prueba del clima a Kafka...")
    producer.send('weather_stream', value=dato_falso)
    producer.flush() 
    print("¡Dato enviado exitosamente! Mirá rápido la consola de Spark EC2.")

except Exception as e:
    print(f"Error al enviar: {e}")
