from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'retries': 0
}

with DAG(
    'orquestador_remoto_spark',
    default_args=default_args,
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:
    
    # Tarea 1: De RAW a REFINED
    etl_refined = SSHOperator(
        task_id='spark_raw_to_refined',
        ssh_conn_id='spark_ec2_ssh',
        cmd_timeout=600,
        do_xcom_push=False,
        command="""
        docker exec spark-master /opt/spark/bin/spark-submit \
            --master spark://spark-master:7077 \
            --deploy-mode client \
            --conf spark.jars.ivy=/tmp/.ivy2 \
            --packages org.apache.hadoop:hadoop-aws:3.4.0,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
            --executor-memory 1g \
            --executor-cores 2 \
            /opt/spark/etl_weather_s3.py
        """
    )

    # Tarea 2: De REFINED a GOLD (Analytics)
    etl_analytics = SSHOperator(
        task_id='spark_refined_to_gold',
        ssh_conn_id='spark_ec2_ssh',
        cmd_timeout=600,
        do_xcom_push=False,
        command="""
        docker exec spark-master /opt/spark/bin/spark-submit \
            --master spark://spark-master:7077 \
            --deploy-mode client \
            --conf spark.jars.ivy=/tmp/.ivy2 \
            --packages org.apache.hadoop:hadoop-aws:3.4.0,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
            --executor-memory 1g \
            --executor-cores 2 \
            /opt/spark/etl_analytics.py
        """
    )

    # Definir la dependencia: Primero pasa a Refined, luego corre Analytics
    etl_refined >> etl_analytics
