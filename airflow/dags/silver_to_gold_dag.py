"""
Silver to Gold Batch DAG

This DAG runs the silver_to_gold.py batch job on the DEDICATED BATCH CLUSTER
(spark-master-batch:7077) every 10 minutes.

IMPORTANT: This uses a completely separate Spark cluster from streaming jobs.
- Streaming cluster: spark-master:7077 (ports 8080, 7077)
- Batch cluster: spark-master-batch:7077 (ports 8083, 7078)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# The spark-submit command to run on the BATCH cluster
# Now includes PostgreSQL JDBC driver for writing gold metrics to Postgres
SPARK_SUBMIT_CMD = """
docker exec tesla-telemetry-spark-master-batch-1 \
    /opt/spark/bin/spark-submit \
    --master spark://spark-master-batch:7077 \
    --deploy-mode client \
    --driver-memory 1g \
    --executor-memory 1g \
    --executor-cores 1 \
    --total-executor-cores 1 \
    --packages org.apache.hadoop:hadoop-aws:3.3.4,org.postgresql:postgresql:42.7.1 \
    /opt/spark/work-dir/spark/batch_jobs/silver_to_gold.py
"""

with DAG(
    dag_id="silver_to_gold_batch",
    default_args=default_args,
    description="Aggregates silver layer data into gold layer metrics",
    schedule_interval="*/10 * * * *",  # Every 10 minutes
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,  # Only one run at a time
    tags=["batch", "gold", "spark"],
) as dag:

    run_silver_to_gold = BashOperator(
        task_id="run_silver_to_gold",
        bash_command=SPARK_SUBMIT_CMD,
    )
