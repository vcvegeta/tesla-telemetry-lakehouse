# 🚗 Tesla Telemetry Lakehouse

A real-time data lakehouse pipeline for Tesla vehicle telemetry data, built with Apache Spark, Kafka, MinIO, and Superset.

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/u/viraat)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

This project demonstrates a production-grade data lakehouse architecture for processing streaming Tesla vehicle telemetry data through Bronze → Silver → Gold layers, with real-time analytics dashboards.

### Key Features

- ⚡ **Real-time Streaming**: Kafka ingestion with Spark Structured Streaming
- 🏗️ **Medallion Architecture**: Bronze (raw) → Silver (clean) → Gold (aggregated) layers
- 📊 **Interactive Dashboards**: Apache Superset with PostgreSQL backend
- 🔄 **Automated Orchestration**: Airflow DAGs for batch processing
- 🐳 **Fully Containerized**: One-command deployment via Docker Compose
- 📈 **Scalable**: Separate Spark clusters for streaming and batch workloads

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

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- 8GB+ RAM recommended
- 20GB+ free disk space

### One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/vcvegeta/tesla-telemetry-lakehouse.git
cd tesla-telemetry-lakehouse

# Start all services
docker-compose up -d

# Wait 2-3 minutes for services to initialize
# Check status
docker-compose ps
```

That's it! All services are now running.

## 📊 Access the Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Spark Master (Streaming)** | http://localhost:8080 | - |
| **Spark Master (Batch)** | http://localhost:8083 | - |
| **Airflow** | http://localhost:8089 | admin / admin |
| **Superset** | http://localhost:8088 | admin / admin |
| **MinIO Console** | http://localhost:9001 | minio / minio12345 |

## 📈 What You'll See

### 1. Real-Time Data Flow

- **Ingestor** generates Tesla telemetry data every 10 seconds
- **Kafka** streams data to Bronze layer
- **Spark Streaming** processes Bronze → Silver with data quality checks
- **Airflow DAG** runs batch aggregations every 10 minutes (Silver → Gold)

### 2. Superset Dashboards

After 10-15 minutes of data accumulation:

1. Open Superset (http://localhost:8088)
2. Login with `admin` / `admin`
3. Navigate to **Dashboards**
4. You'll see:
   - **Tesla Battery Level Over Time** (line chart)
   - **Telemetry Events Per Minute** (bar chart)
   - Auto-refreshes every 10 minutes

### 3. Airflow Monitoring

1. Open Airflow (http://localhost:8089)
2. Check the `silver_to_gold_batch` DAG
3. See successful runs every 10 minutes

## 🗂️ Data Layers

### Bronze Layer (Raw Data)
- **Location**: MinIO `s3a://lakehouse/bronze/telemetry_raw/`
- **Format**: Parquet
- **Schema**: Raw JSON from Kafka
- **Processing**: Exactly-once from Kafka

### Silver Layer (Cleaned Data)
- **Location**: MinIO `s3a://lakehouse/silver/telemetry_clean/`
- **Format**: Parquet with explicit schema
- **Processing**: Data quality checks, type casting, deduplication

### Gold Layer (Aggregated Metrics)
- **Location**: 
  - MinIO `s3a://lakehouse/gold/vehicle_minute_metrics/`
  - PostgreSQL `gold_vehicle_minute_metrics` table
- **Metrics**: Per-vehicle and fleet-wide aggregations
- **Refresh**: Every 10 minutes via Airflow

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Data Ingestion** | Kafka 7.6.1 | Stream processing |
| **Stream Processing** | Apache Spark 3.5.1 | Real-time ETL |
| **Batch Processing** | Apache Spark 3.5.1 | Scheduled aggregations |
| **Orchestration** | Apache Airflow 2.9.3 | Workflow management |
| **Storage** | MinIO (S3-compatible) | Data lakehouse |
| **Database** | PostgreSQL 16 | Gold layer storage |
| **Visualization** | Apache Superset 4.1.0 | Dashboards |
| **Language** | Python 3.11 | All data processing logic |

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

## 📝 Project Structure

```
tesla-telemetry-lakehouse/
├── docker-compose.yml          # Main orchestration file
├── Dockerfile.spark            # Custom Spark image
├── Dockerfile.airflow          # Custom Airflow image
├── Dockerfile.ingestor         # Data generator image
├── airflow/
│   └── dags/
│       └── silver_to_gold_dag.py   # Batch processing DAG
├── spark/
│   ├── streaming_jobs/
│   │   ├── kafka_to_minio_bronze.py    # Kafka → Bronze
│   │   └── bronze_to_silver.py         # Bronze → Silver
│   └── batch_jobs/
│       └── silver_to_gold.py           # Silver → Gold
└── services/
    └── ingestor/
        └── ingest.py           # Tesla data generator
```

## 🎓 Use Cases

This project demonstrates:

- ✅ **Data Engineering**: End-to-end lakehouse implementation
- ✅ **Stream Processing**: Real-time data pipelines with Spark Structured Streaming
- ✅ **Batch Processing**: Scheduled aggregations with Airflow
- ✅ **Data Architecture**: Medallion (Bronze/Silver/Gold) pattern
- ✅ **DevOps**: Containerization and orchestration
- ✅ **Data Visualization**: Business intelligence dashboards

Perfect for:
- Data Engineer portfolio projects
- Learning modern data stack
- Interview preparation
- Architecture reference

## 🐛 Troubleshooting

### Services not starting?

```bash
# Check logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>
```

### High memory usage?

```bash
# Check Docker memory
docker stats

# Reduce worker memory in docker-compose.yml
SPARK_WORKER_MEMORY: 1g
```

### Data not appearing in Superset?

1. Wait 10-15 minutes for initial data accumulation
2. Check Airflow DAG has run successfully
3. Verify PostgreSQL has data:
   ```bash
   docker exec -it tesla-telemetry-postgres-1 psql -U airflow -d lakehouse -c "SELECT COUNT(*) FROM gold_vehicle_minute_metrics;"
   ```

## 🤝 Contributing

This is a portfolio/educational project. Feel free to fork and adapt for your needs!

## 📄 License

MIT License - feel free to use this project for learning and portfolio purposes.

## 👤 Author

**Viraat Chaudhary**
- GitHub: [@vcvegeta](https://github.com/vcvegeta)
- Docker Hub: [viraat](https://hub.docker.com/u/viraat)

## 🌟 Acknowledgments

Built with:
- Apache Spark
- Apache Kafka
- Apache Airflow
- Apache Superset
- MinIO
- PostgreSQL

---

**⭐ If this project helped you, please star it on GitHub!**
