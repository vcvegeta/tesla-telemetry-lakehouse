# 🚗 Tesla Telemetry Lakehouse

A real-time data lakehouse pipeline for Tesla vehicle telemetry data, built with Apache Spark, Kafka, MinIO, and Superset.

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/u/viraat)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A production-ready data lakehouse implementation processing Tesla vehicle telemetry through the medallion architecture (Bronze → Silver → Gold layers). The entire pipeline runs in Docker containers with automated initialization.

**What makes this different:** Everything auto-configures on startup. No manual database connections, no manual dashboard setup. Just run `docker-compose up -d` and you're ready.

### Technical Stack

- **Stream Processing**: Apache Spark Structured Streaming with Kafka
- **Data Storage**: MinIO (S3-compatible object storage) + PostgreSQL
- **Orchestration**: Apache Airflow for batch jobs
- **Visualization**: Apache Superset with programmatic dashboard creation
- **Architecture**: Medallion pattern (Bronze/Silver/Gold) with separate Spark clusters for streaming and batch workloads

## 🏛️ Architecture

```
┌─────────────┐      ┌────────┐      ┌─────────────────┐
│   Ingestor  │─────▶│ Kafka  │─────▶│ Spark Streaming │
│ (Telemetry) │      │        │      │   (Bronze)      │
└─────────────┘      └────────┘      └────────┬────────┘
                                               │
                                               ▼
┌─────────────┐      ┌────────────────────────┴───────┐
│  MinIO S3   │◀─────┤    Medallion Lakehouse        │
│  Storage    │      │  Bronze │ Silver │ Gold        │
└──────┬──────┘      └────────────────────────────────┘
       │                      │              │
       │                      ▼              ▼
       │             ┌───────────────┐  ┌──────────────┐
       │             │ Spark Stream  │  │ Spark Batch  │
       │             │   (Silver)    │  │   (Gold)     │
       │             └───────────────┘  └──────┬───────┘
       │                                       │
       ▼                                       ▼
  ┌─────────┐                        ┌────────────────┐
  │ Airflow │                        │  PostgreSQL    │
  │  DAGs   │                        │  (Gold Layer)  │
  └─────────┘                        └────────┬───────┘
                                              │
                                              ▼
                                     ┌────────────────┐
                                     │    Superset    │
                                     │   Dashboards   │
                                     └────────────────┘
```

## Quick Start

**Requirements:**
- Docker Desktop (or Docker Engine + Docker Compose)
- 8GB RAM minimum
- 20GB free disk space

**Deploy:**

```bash
git clone https://github.com/vcvegeta/tesla-telemetry-lakehouse.git
cd tesla-telemetry-lakehouse/infra
docker-compose up -d
```

Wait 2-3 minutes for initialization. All services start automatically:
- MinIO creates the `lakehouse` bucket
- PostgreSQL initializes the database schema
- Superset creates database connections, datasets, charts, and dashboards
- Airflow loads the batch processing DAG
- Streaming jobs begin processing Kafka events

Dashboards populate with data within 10-15 minutes as events flow through the pipeline.

## Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Superset (Dashboards) | http://localhost:8088 | admin / admin |
| Airflow (Orchestration) | http://localhost:8089 | admin / admin |
| Spark Master (Streaming) | http://localhost:8080 | - |
| Spark Master (Batch) | http://localhost:8083 | - |
| MinIO Console | http://localhost:9001 | minio / minio12345 |

## Data Flow

### Pipeline Overview

The ingestor generates mock Tesla telemetry events every 10 seconds and publishes them to Kafka. Two separate data processing paths handle the transformation:

**Streaming Path (Bronze → Silver):**
- Spark Structured Streaming consumes from Kafka in micro-batches
- Raw events land in MinIO as Bronze layer Parquet files
- A second streaming job applies schema validation and data quality checks
- Cleaned records write to the Silver layer in MinIO

**Batch Path (Silver → Gold):**
- Airflow triggers a Spark batch job every 10 minutes
- Reads Silver layer data and computes aggregations (per-vehicle and fleet-wide)
- Writes aggregated metrics to PostgreSQL gold tables
- Superset queries PostgreSQL to render dashboard charts

### Superset Dashboards

On first startup, an initialization script creates:
- Database connection to PostgreSQL
- Two datasets (gold_vehicle_minute_metrics, gold_fleet_minute_metrics)
- Two charts (Battery Level Over Time, Events Per Minute)
- A dashboard containing both charts

Access the dashboard:
1. Navigate to http://localhost:8088
2. Login: admin / admin
3. Go to Dashboards → Tesla Fleet Dashboard

Charts populate with data after 10-15 minutes once the pipeline processes events through all three layers.

The automation works by directly inserting records into Superset's SQLite metadata database during container initialization. This survives `docker-compose down -v` restarts. See [SUPERSET_DASHBOARD.md](SUPERSET_DASHBOARD.md) for implementation details.

### Airflow

The `silver_to_gold_batch` DAG runs every 10 minutes, triggering a Spark job that reads from the Silver layer and writes aggregated metrics to PostgreSQL. View DAG runs at http://localhost:8089.

## Data Layers

**Bronze Layer** (`s3a://lakehouse/bronze/telemetry_raw/`)
- Raw events from Kafka stored as Parquet
- Exactly-once semantics with Kafka offset management
- No schema enforcement at this stage

**Silver Layer** (`s3a://lakehouse/silver/telemetry_clean/`)
- Validated and typed Parquet files
- Data quality filters applied (non-null checks, range validation)
- Deduplication based on event_id and timestamp

**Gold Layer** (PostgreSQL + MinIO)
- Minute-level aggregations: `gold_vehicle_minute_metrics`, `gold_fleet_minute_metrics`
- Computed metrics: avg_battery_level, avg_speed, total_events per time window
- Refreshed every 10 minutes by Airflow-triggered Spark jobs

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|----------|
| Stream Processing | Apache Spark | 3.5.1 |
| Message Queue | Apache Kafka | 7.6.1 |
| Orchestration | Apache Airflow | 2.9.3 |
| Object Storage | MinIO | Latest |
| Database | PostgreSQL | 16 |
| Visualization | Apache Superset | 4.1.0 |
| Language | Python | 3.11 |

## 🔧 Configuration

### Environment Variables

All configuration is in `docker-compose.yml`. Key settings:

```yaml
# MinIO credentials
MINIO_ROOT_USER: minio
MINIO_ROOT_PASSWORD: minio12345

# PostgreSQL
POSTGRES_USER: airflow
POSTGRES_PASSWORD: airflow

# Kafka
KAFKA_BOOTSTRAP_SERVERS: kafka:9092
```

### Resource Allocation

Current configuration (adjust for your system):

```yaml
# Spark Workers
SPARK_WORKER_CORES: 2
SPARK_WORKER_MEMORY: 2g

# Streaming Jobs
--driver-memory 1g
--executor-memory 1g
```

## Project Structure

```
tesla-telemetry-lakehouse/
├── README.md
├── SUPERSET_DASHBOARD.md
├── infra/
│   ├── docker-compose.yml
│   └── superset/
│       ├── Dockerfile
│       ├── superset-init.sh
│       └── create_charts.py
├── airflow/
│   └── dags/
│       └── silver_to_gold_dag.py
├── spark/
│   ├── streaming_jobs/
│   │   ├── kafka_to_minio_bronze.py
│   │   └── bronze_to_silver.py
│   └── batch_jobs/
│       └── silver_to_gold.py
└── services/
    ├── ingestor/
    │   └── ingest.py
    └── outage_detector/
        └── outage_detector.py
```

## Use Cases

This project demonstrates:

- End-to-end data lakehouse implementation with medallion architecture
- Stream processing with Spark Structured Streaming
- Batch orchestration using Airflow
- Infrastructure as code with Docker Compose
- Programmatic dashboard creation and deployment automation

Suitable for portfolio projects, technical interviews, and learning modern data engineering patterns. The automated setup makes it easy to demonstrate during presentations.

## Troubleshooting

**Services won't start:**
```bash
docker-compose logs <service-name>
docker-compose restart <service-name>
```

**High memory usage:**
Reduce worker memory in `docker-compose.yml`:
```yaml
SPARK_WORKER_MEMORY: 1g
```

**Empty charts in Superset:**

This is normal for the first 10-15 minutes. Data flows through the pipeline in stages:
- Minutes 0-5: Events land in Bronze layer from Kafka
- Minutes 5-10: Streaming job processes Bronze to Silver
- Minutes 10-15: Batch job aggregates Silver to Gold (charts populate)

Verify data exists:
```bash
docker exec tesla-telemetry-postgres-1 psql -U airflow -d lakehouse -c "SELECT COUNT(*) FROM gold_vehicle_minute_metrics;"
```

Verify dashboard creation:
```bash
docker logs tesla-telemetry-superset-1 | grep "setup complete"
```

**Test full automation:**
```bash
cd infra
docker-compose down -v  # Delete all volumes
docker-compose up -d     # Everything recreates automatically
```

## License

MIT License

## Author

Viraat Chaudhary  
GitHub: [@vcvegeta](https://github.com/vcvegeta)  
Docker Hub: [viraat](https://hub.docker.com/u/viraat)
