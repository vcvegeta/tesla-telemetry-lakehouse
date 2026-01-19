# 🚗 Tesla Telemetry Lakehouse

A real-time data lakehouse pipeline for Tesla vehicle telemetry data, built with Apache Spark, Kafka, MinIO, and Superset.

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/u/viraat)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📊 Dashboard Preview

![Tesla Fleet Dashboard](docs/images/tesla_fleet_dashboard.png)

*Sample Superset dashboard showing real-time battery levels and telemetry event metrics. Created in ~5 minutes following the [Dashboard Guide](infra/DASHBOARD_GUIDE.md).*

---

## Overview

A production-ready data lakehouse implementation processing Tesla vehicle telemetry through the medallion architecture (Bronze → Silver → Gold layers). The entire pipeline runs in Docker containers with automated initialization.

**What makes this different:** Everything auto-configures on startup. PostgreSQL database connection is created automatically in Superset. Just run `docker-compose up -d`, wait for data to populate, then create your custom dashboards in minutes.

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
- Superset creates database connection to PostgreSQL automatically
- Airflow loads the batch processing DAG
- Streaming jobs begin processing Kafka events

Data populates within 10-15 minutes. Then follow [`infra/DASHBOARD_GUIDE.md`](infra/DASHBOARD_GUIDE.md) to create your custom dashboards (~5 minutes).

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

**What's Automated:**
On first startup, Superset automatically:
- ✅ Creates database connection to PostgreSQL (`Tesla Lakehouse`)
- ✅ Installs PostgreSQL driver (psycopg2-binary)
- ✅ Initializes admin user (username: `admin`, password: `admin`)

**Your Part (~5 minutes):**
Create custom visualizations following the guide in [`infra/DASHBOARD_GUIDE.md`](infra/DASHBOARD_GUIDE.md):

1. Login to Superset: http://localhost:8088 (admin/admin)
2. Create dataset from `gold_vehicle_minute_metrics` table
3. Build 2 example charts:
   - **Battery Level Over Time** (Line Chart) - `MIN(min_battery_percent)` by `minute_ts`
   - **Events Per Minute** (Bar Chart) - `SUM(event_count)` by `minute_ts`
4. Add charts to a dashboard

**Available Data Tables:**

*Table: `gold_vehicle_minute_metrics`*

![Vehicle Metrics Columns](docs/images/gold_vehicle_minute_metrics_columns.png)

| Column | Type | Description |
|--------|------|-------------|
| `vehicle_id` | TEXT | Unique vehicle identifier |
| `minute_ts` | TIMESTAMP | Minute-level timestamp |
| `avg_speed_mph` | DOUBLE | Average speed in MPH |
| `max_speed_mph` | DOUBLE | Maximum speed in MPH |
| `min_battery_percent` | INTEGER | Minimum battery percentage |
| `event_count` | BIGINT | Total telemetry events |

*Table: `gold_fleet_minute_metrics`*

![Fleet Metrics Columns](docs/images/gold_fleet_minute_metrics_columns.png)

| Column | Type | Description |
|--------|------|-------------|
| `minute_ts` | TIMESTAMP | Minute-level timestamp |
| `avg_speed_mph_fleet` | DOUBLE | Fleet average speed |
| `min_battery_percent_fleet` | INTEGER | Fleet minimum battery |
| `total_events` | BIGINT | Total fleet events |

**Why manual chart creation?** This gives you flexibility to build custom visualizations tailored to your needs. Superset supports 50+ chart types - create as many dashboards as you want!

Charts populate with data after 10-15 minutes once the pipeline processes events through all layers.

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

## 🎯 What's Automated

This project emphasizes automation while giving you creative control over visualizations:

### ✅ Fully Automated (Zero Manual Steps):
- **Infrastructure Setup**: All containers auto-configure on startup
- **MinIO Initialization**: Lakehouse bucket created automatically
- **PostgreSQL Setup**: Database and tables initialized
- **Superset Database Connection**: PostgreSQL connection pre-configured
- **Superset Admin User**: Login credentials ready (admin/admin)
- **Data Pipeline**: Streaming and batch jobs start automatically
- **Airflow DAGs**: Batch processing scheduled every 10 minutes

### 👤 User-Created (~5 minutes):
- **Dashboards & Charts**: Build custom visualizations using Superset UI
  - Follow step-by-step guide: [`infra/DASHBOARD_GUIDE.md`](infra/DASHBOARD_GUIDE.md)
  - Create as many charts as needed (line, bar, table, heatmap, etc.)
  - Full flexibility to design dashboards for your use case

**Why this approach?** Database connections are tedious to set up repeatedly, so we automated them. Chart creation is fast, creative, and gives you control over your analytics layer. Best of both worlds!

---

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
├── infra/
│   ├── docker-compose.yml
│   ├── DASHBOARD_GUIDE.md          # Step-by-step dashboard creation
│   └── superset/
│       ├── Dockerfile
│       └── superset-init.sh        # Auto-creates DB connection
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
- Real-time stream processing with Spark Structured Streaming
- Batch orchestration using Airflow
- Infrastructure as code with Docker Compose
- Automated database connection setup for Superset
- Production-ready deployment with proper resource isolation

Suitable for portfolio projects, technical interviews, and learning modern data engineering patterns. The streamlined setup makes it easy to demonstrate during presentations.

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
- Minutes 10-15: Batch job aggregates Silver to Gold (PostgreSQL tables ready)

After ~15 minutes, follow [`infra/DASHBOARD_GUIDE.md`](infra/DASHBOARD_GUIDE.md) to create dashboards.

Verify data exists:
```bash
docker exec tesla-telemetry-postgres-1 psql -U airflow -d lakehouse -c "SELECT COUNT(*) FROM gold_vehicle_minute_metrics;"
```

Verify database connection:
```bash
docker logs tesla-telemetry-superset-1 | grep "Database connection"
# Should show: ✅ Database connection 'Tesla Lakehouse' created successfully!
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
