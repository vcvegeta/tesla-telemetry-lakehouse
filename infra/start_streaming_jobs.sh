#!/bin/bash

cd "$(dirname "$0")"

echo "🔄 Cleaning checkpoints..."
docker compose exec -T minio rm -rf /data/lakehouse/_checkpoints/telemetry_raw
docker compose exec -T minio rm -rf /data/lakehouse/_checkpoints/silver/telemetry_clean

echo ""
echo "🚀 Starting Kafka → Bronze (streaming)..."
nohup docker compose exec -T spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --executor-cores 2 \
  --total-executor-cores 4 \
  --driver-memory 2g \
  --executor-memory 2g \
  --conf spark.jars.ivy=/tmp/.ivy2 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.hadoop:hadoop-aws:3.3.4 \
  /opt/spark/work-dir/spark/streaming_jobs/kafka_to_minio_bronze.py \
  > /tmp/kafka_to_bronze.log 2>&1 &

KAFKA_PID=$!
echo "   PID: $KAFKA_PID"

sleep 15

echo ""
echo "🚀 Starting Bronze → Silver (streaming)..."
nohup docker compose exec -T spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --executor-cores 2 \
  --total-executor-cores 4 \
  --driver-memory 2g \
  --executor-memory 2g \
  --conf spark.jars.ivy=/tmp/.ivy2 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4 \
  /opt/spark/work-dir/spark/streaming_jobs/bronze_to_silver.py \
  > /tmp/bronze_to_silver.log 2>&1 &

BRONZE_PID=$!
echo "   PID: $BRONZE_PID"

echo ""
echo "✅ Both streaming jobs started!"
echo ""
echo "📊 Monitor logs:"
echo "   Kafka→Bronze:  tail -f /tmp/kafka_to_bronze.log"
echo "   Bronze→Silver: tail -f /tmp/bronze_to_silver.log"
echo ""
echo "🌐 Spark UI: http://localhost:8080"
echo ""
echo "⏳ Waiting 60 seconds for jobs to initialize..."
sleep 60

echo ""
echo "📁 Checking data..."
echo "=== BRONZE ==="
docker compose exec -T minio ls -ltr /data/lakehouse/bronze/telemetry_raw/ 2>&1 | tail -3

echo ""
echo "=== SILVER ==="
docker compose exec -T minio ls -ltr /data/lakehouse/silver/telemetry_clean/ 2>&1 | tail -3
