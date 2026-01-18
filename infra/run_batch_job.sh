#!/bin/bash

cd "$(dirname "$0")"

echo "🔄 Running Silver → Gold (batch job)..."
echo ""

docker compose exec -T spark-master-batch /opt/spark/bin/spark-submit \
  --master spark://spark-master-batch:7077 \
  --deploy-mode client \
  --executor-cores 2 \
  --total-executor-cores 2 \
  --driver-memory 2g \
  --executor-memory 2g \
  --conf spark.jars.ivy=/tmp/.ivy2 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4 \
  /opt/spark/work-dir/spark/batch_jobs/silver_to_gold.py

echo ""
echo "✅ Batch job completed!"
echo ""
echo "📁 Checking gold data..."
echo "=== GOLD: Vehicle Metrics ==="
docker compose exec -T minio ls -ltr /data/lakehouse/gold/vehicle_minute_metrics/ 2>&1 | tail -3

echo ""
echo "=== GOLD: Fleet Metrics ==="
docker compose exec -T minio ls -ltr /data/lakehouse/gold/fleet_minute_metrics/ 2>&1 | tail -3
