from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_trunc, avg, min as fmin, max as fmax, count
import os

SILVER_PATH = "s3a://lakehouse/silver/telemetry_clean/"
GOLD_VEHICLE_MINUTE = "s3a://lakehouse/gold/vehicle_minute_metrics/"
GOLD_FLEET_MINUTE   = "s3a://lakehouse/gold/fleet_minute_metrics/"

# PostgreSQL connection details
POSTGRES_URL = "jdbc:postgresql://postgres:5432/lakehouse"
POSTGRES_USER = "airflow"
POSTGRES_PASSWORD = "airflow"

# S3A / MinIO settings - MUST be set BEFORE SparkSession creation
spark = SparkSession.builder \
    .appName("silver-to-gold-batch") \
    .master("spark://spark-master-batch:7077") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.7.1") \
    .config("fs.s3a.endpoint", "http://minio:9000") \
    .config("fs.s3a.path.style.access", "true") \
    .config("fs.s3a.connection.ssl.enabled", "false") \
    .config("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .config("fs.s3a.access.key", os.environ.get("AWS_ACCESS_KEY_ID", "minio")) \
    .config("fs.s3a.secret.key", os.environ.get("AWS_SECRET_ACCESS_KEY", "minio12345")) \
    .config("fs.s3a.signing-algorithm", "S3SignerType") \
    .config("fs.s3a.connection.establish.timeout", "5000") \
    .config("fs.s3a.connection.timeout", "10000") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Also set on Hadoop config for good measure
hconf = spark._jsc.hadoopConfiguration()
hconf.set("fs.s3a.endpoint", "http://minio:9000")
hconf.set("fs.s3a.path.style.access", "true")
hconf.set("fs.s3a.connection.ssl.enabled", "false")
hconf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
hconf.set("fs.s3a.access.key", os.environ.get("AWS_ACCESS_KEY_ID", "minio"))
hconf.set("fs.s3a.secret.key", os.environ.get("AWS_SECRET_ACCESS_KEY", "minio12345"))
hconf.set("fs.s3a.signing-algorithm", "S3SignerType")
hconf.set("fs.s3a.connection.establish.timeout", "5000")
hconf.set("fs.s3a.connection.timeout", "10000")

# Read ALL silver (batch)
silver = spark.read.parquet(SILVER_PATH)

# Create a minute bucket
silver = silver.withColumn("minute_ts", date_trunc("minute", col("event_ts")))

# 1) Per-vehicle per-minute aggregates
vehicle_minute = (
    silver.groupBy("vehicle_id", "minute_ts")
    .agg(
        avg("speed_mph").alias("avg_speed_mph"),
        fmax("speed_mph").alias("max_speed_mph"),
        fmin("battery_percent").alias("min_battery_percent"),
        count("*").alias("event_count"),
    )
)

# 2) Fleet-wide per-minute aggregates
fleet_minute = (
    silver.groupBy("minute_ts")
    .agg(
        avg("speed_mph").alias("avg_speed_mph_fleet"),
        fmin("battery_percent").alias("min_battery_percent_fleet"),
        count("*").alias("total_events"),
    )
)

# Write (overwrite) — batch job recomputes Gold each run
# 1. Write to MinIO (keeps lakehouse intact)
vehicle_minute.write.mode("overwrite").parquet(GOLD_VEHICLE_MINUTE)
fleet_minute.write.mode("overwrite").parquet(GOLD_FLEET_MINUTE)

# 2. Write to PostgreSQL (for Superset dashboards)
print("📊 Writing to PostgreSQL for Superset...")
vehicle_minute.write \
    .format("jdbc") \
    .option("url", POSTGRES_URL) \
    .option("dbtable", "gold_vehicle_minute_metrics") \
    .option("user", POSTGRES_USER) \
    .option("password", POSTGRES_PASSWORD) \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()

fleet_minute.write \
    .format("jdbc") \
    .option("url", POSTGRES_URL) \
    .option("dbtable", "gold_fleet_minute_metrics") \
    .option("user", POSTGRES_USER) \
    .option("password", POSTGRES_PASSWORD) \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()

print("✅ Gold batch written successfully to MinIO and PostgreSQL.")

