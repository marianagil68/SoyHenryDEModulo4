import os
from dotenv import load_dotenv

load_dotenv()
import boto3
from datetime import datetime
import gzip
import json

# configuración
BUCKET = "datalake-energy-dev-marianagil"

STREAM_PREFIXES = {
    "weather_patagonia": "raw/ingesta-tiempo-real/weather_patagonia/",
    "weather_riohacha": "raw/ingesta-tiempo-real/weather_riohacha/",
}

HIST_PREFIXES = {
    "weather_patagonia": "raw/historicos/weather_patagonia/",
    "weather_riohacha": "raw/historicos/weather_riohacha/",
}

# cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
)

def get_latest_key(prefix: str) -> str | None:
    paginator = s3.get_paginator("list_objects_v2")

    latest_key = None
    latest_time = None

    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue

            lm = obj["LastModified"]
            if latest_time is None or lm > latest_time:
                latest_time = lm
                latest_key = key

    return latest_key

def copy_latest_to_history(dataset: str):
    src_prefix = STREAM_PREFIXES[dataset]
    dst_prefix = HIST_PREFIXES[dataset]

    latest_key = get_latest_key(src_prefix)
    if not latest_key:
        print(f"[{dataset}] No se encontraron archivos en {src_prefix}")
        return

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = latest_key.split("/")[-1]
    dst_key = f"{dst_prefix}{ts}_{filename}"

    s3.copy_object(
        Bucket=BUCKET,
        CopySource={"Bucket": BUCKET, "Key": latest_key},
        Key=dst_key,
    )

    print(f"[{dataset}] OK: {latest_key} -> {dst_key}")

if __name__ == "__main__":
    for dataset in STREAM_PREFIXES.keys():
        copy_latest_to_history(dataset)