from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, cast, coalesce
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
import os

KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC = "telemetry_raw"
S3_ENDPOINT = "http://minio:9000"
S3_BUCKET = "lakehouse"
OUTPUT_PATH = f"s3a://{S3_BUCKET}/bronze/telemetry_raw/"
CHECKPOINT_PATH = f"s3a://{S3_BUCKET}/_checkpoints/telemetry_raw/"

schema = StructType([
    StructField("event_id", StringType()),
    StructField("vehicle_id", StringType()),
    StructField("event_time", StringType()),
    StructField("ingest_time", StringType()),
    StructField("source", StringType()),
    StructField("payload", StructType([
        StructField("battery_percent", IntegerType()),
        StructField("speed_mph", DoubleType()),
        StructField("odometer_miles", DoubleType()),
    ])),
])

# S3A / MinIO settings - MUST be set BEFORE SparkSession creation
spark = (
    SparkSession.builder
    .appName("kafka-to-minio-bronze")
    .config("fs.s3a.endpoint", S3_ENDPOINT)
    .config("fs.s3a.path.style.access", "true")
    .config("fs.s3a.connection.ssl.enabled", "false")
    .config("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    .config("fs.s3a.access.key", os.environ.get("AWS_ACCESS_KEY_ID", "minio"))
    .config("fs.s3a.secret.key", os.environ.get("AWS_SECRET_ACCESS_KEY", "minio12345"))
    .config("fs.s3a.signing-algorithm", "S3SignerType")
    .config("fs.s3a.connection.establish.timeout", "5000")
    .config("fs.s3a.connection.timeout", "10000")
    .getOrCreate()
)

# Also set on Hadoop config for good measure
hconf = spark._jsc.hadoopConfiguration()
hconf.set("fs.s3a.endpoint", S3_ENDPOINT)
hconf.set("fs.s3a.path.style.access", "true")
hconf.set("fs.s3a.connection.ssl.enabled", "false")
hconf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
hconf.set("fs.s3a.access.key", os.environ.get("AWS_ACCESS_KEY_ID", "minio"))
hconf.set("fs.s3a.secret.key", os.environ.get("AWS_SECRET_ACCESS_KEY", "minio12345"))
hconf.set("fs.s3a.signing-algorithm", "S3SignerType")
hconf.set("fs.s3a.connection.establish.timeout", "5000")
hconf.set("fs.s3a.connection.timeout", "10000")


df_kafka = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", TOPIC)
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .load()
)

# Cast value to string and parse JSON
json_str = df_kafka.selectExpr("CAST(value AS STRING) as json")
parsed_flat = json_str.select(from_json(col("json"), schema).alias("data")).select("data.*")

query = (
    parsed_flat.writeStream
    .format("parquet")
    .option("path", OUTPUT_PATH)
    .option("checkpointLocation", CHECKPOINT_PATH)
    .outputMode("append")
    .trigger(processingTime="5 seconds")
    .start()
)

print("✅ Kafka-to-Bronze streaming job started successfully!")
print(f"Writing to: {OUTPUT_PATH}")
print(f"Checkpoint: {CHECKPOINT_PATH}")

query.awaitTermination()
