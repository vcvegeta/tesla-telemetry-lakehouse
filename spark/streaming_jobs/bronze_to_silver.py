from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
import os

# S3A / MinIO settings - MUST be set BEFORE SparkSession creation
spark = (
    SparkSession.builder
    .appName("bronze-to-silver")
    .config("fs.s3a.endpoint", "http://minio:9000")
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

spark.sparkContext.setLogLevel("WARN")
spark.conf.set("spark.sql.shuffle.partitions", "2")

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

BRONZE_PATH = "s3a://lakehouse/bronze/telemetry_raw/"
SILVER_PATH = "s3a://lakehouse/silver/telemetry_clean/"
CHECKPOINT  = "s3a://lakehouse/_checkpoints/silver/telemetry_clean/"

# Define schema explicitly to avoid blocking read
bronze_schema = StructType([
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

# Use that schema for streaming read
bronze = (
    spark.readStream
    .schema(bronze_schema)
    .format("parquet")
    .option("maxFilesPerTrigger", 1)
    .option("latestFirst", "true")
    .option("recursiveFileLookup", "true")
    .option("ignoreDeletes", "true")
    .load(BRONZE_PATH)
)

silver = (
    bronze
    .withColumn("event_ts", to_timestamp(col("event_time")))
    .withColumn("ingest_ts", to_timestamp(col("ingest_time")))
    .select(
        "event_id",
        "vehicle_id",
        "source",
        "event_ts",
        "ingest_ts",
        col("payload.battery_percent").alias("battery_percent"),
        col("payload.speed_mph").alias("speed_mph"),
        col("payload.odometer_miles").alias("odometer_miles"),
    )
    .filter(col("battery_percent").between(0, 100))
    .filter(col("speed_mph") >= 0)
)

query = (
    silver.writeStream
    .format("parquet")
    .option("path", SILVER_PATH)
    .option("checkpointLocation", CHECKPOINT)
    .outputMode("append")
    .trigger(processingTime="5 seconds")
    .start()
)

print("✅ Bronze-to-Silver streaming job started successfully!")
print(f"Reading from: {BRONZE_PATH}")
print(f"Writing to: {SILVER_PATH}")
print(f"Checkpoint: {CHECKPOINT}")

query.awaitTermination()
