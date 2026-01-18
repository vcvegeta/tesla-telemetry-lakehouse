# Tesla Telemetry Lakehouse - Backup Checklist ✅

**Date**: January 17, 2026  
**Status**: All files saved and committed to Git  
**GitHub**: https://github.com/vcvegeta/tesla-telemetry-lakehouse  
**Docker Hub**: https://hub.docker.com/u/viraat

---

## 📦 Core Project Files (Root Directory)

- ✅ `README.md` - Complete documentation with architecture
- ✅ `docker-compose.yml` - Production deployment (uses Docker Hub images)
- ✅ `.gitignore` - Excludes logs and cache files
- ✅ `Dockerfile.spark` - Custom Spark image build
- ✅ `Dockerfile.airflow` - Custom Airflow image build
- ✅ `Dockerfile.ingestor` - Custom data generator image build

---

## 🔄 Airflow DAGs

**Location**: `airflow/dags/`

- ✅ `silver_to_gold_dag.py` - Batch processing DAG (runs every 10 minutes)

**Configuration**:
- Schedule: `*/10 * * * *` (every 10 minutes)
- Target: Batch Spark cluster (spark-master-batch:7077)
- Packages: hadoop-aws, postgresql JDBC

---

## ⚡ Spark Jobs

### Streaming Jobs
**Location**: `spark/streaming_jobs/`

- ✅ `kafka_to_minio_bronze.py` - Kafka → Bronze layer
  - Reads from Kafka topic "telemetry_raw"
  - Writes to s3a://lakehouse/bronze/telemetry_raw/
  - Checkpoint: s3a://lakehouse/_checkpoints/bronze/telemetry_raw/

- ✅ `bronze_to_silver.py` - Bronze → Silver transformation
  - Reads from Bronze layer
  - Schema enforcement and data quality checks
  - Writes to s3a://lakehouse/silver/telemetry_clean/
  - Checkpoint: s3a://lakehouse/_checkpoints/silver/telemetry_clean/

### Batch Jobs
**Location**: `spark/batch_jobs/`

- ✅ `silver_to_gold.py` - Silver → Gold aggregation
  - Aggregates to minute-level metrics
  - **Dual writes**: MinIO (Parquet) + PostgreSQL (for Superset)
  - Vehicle metrics: s3a://lakehouse/gold/vehicle_minute_metrics/
  - Fleet metrics: s3a://lakehouse/gold/fleet_minute_metrics/
  - PostgreSQL tables: gold_vehicle_minute_metrics, gold_fleet_minute_metrics

---

## 🔧 Services

### Data Ingestor
**Location**: `services/ingestor/`

- ✅ `ingest.py` - Tesla telemetry data generator
- ✅ `requirements.txt` - Python dependencies (kafka-python)
- ✅ `Dockerfile` - Original build file (optional, Dockerfile.ingestor in root is used)

**Behavior**:
- Generates data every 10 seconds
- Sends to Kafka topic "telemetry_raw"
- Simulates stationary vehicle (speed=0, battery=80%)

---

## 🏗️ Infrastructure Files

**Location**: `infra/`

- ✅ `docker-compose.yml` - Original development version (with build contexts)
- ✅ `docker-compose.yml.bak` - Backup of original
- ✅ `run_batch_job.sh` - Manual batch job trigger script
- ✅ `start_streaming_jobs.sh` - Manual streaming jobs starter
- ✅ `spark/Dockerfile` - Original Spark Dockerfile
- ✅ `superset/Dockerfile` - Original Superset Dockerfile

**Note**: Production deployment uses `/docker-compose.yml` in project root

---

## 🐳 Docker Hub Images (Published)

- ✅ `viraat/tesla-telemetry-spark:latest`
  - Digest: sha256:ca7b39c5...
  - Contains: All Spark streaming and batch jobs
  - Pre-downloaded: hadoop-aws, spark-sql-kafka, postgresql JDBC

- ✅ `viraat/tesla-telemetry-airflow:latest`
  - Digest: sha256:cb7e5800...
  - Contains: Airflow DAGs + Docker CLI

- ✅ `viraat/tesla-telemetry-ingestor:latest`
  - Digest: sha256:2d244b15...
  - Contains: Data generator script

---

## 📊 Database Schemas

### PostgreSQL `lakehouse` Database

**Table**: `gold_vehicle_minute_metrics`
```sql
- vin (VARCHAR)
- window_start (TIMESTAMP)
- window_end (TIMESTAMP)
- avg_battery_level (DOUBLE)
- avg_speed (DOUBLE)
- total_events (BIGINT)
```
**Current Data**: 496 records (as of last check)

**Table**: `gold_fleet_minute_metrics`
```sql
- window_start (TIMESTAMP)
- window_end (TIMESTAMP)
- total_vehicles (BIGINT)
- avg_battery_level (DOUBLE)
- avg_speed (DOUBLE)
- total_events (BIGINT)
```
**Current Data**: 0 records (fleet data in MinIO only)

---

## 📈 Superset Configuration

### Dashboards Created
- ✅ **Tesla Fleet Dashboard** (auto-refresh: 10 minutes)

### Charts Created
1. **Tesla Battery Level Over Time**
   - Type: Line chart
   - X-axis: window_start (minute granularity)
   - Y-axis: avg_battery_level
   - Data: 376-456 rows

2. **Tesla Telemetry Events Per Minute**
   - Type: Bar chart
   - X-axis: window_start (minute granularity)
   - Y-axis: total_events
   - Data: 376-456 rows

### Database Connection
- Database: PostgreSQL
- URI: `postgresql://airflow:airflow@postgres:5432/lakehouse`
- Driver: psycopg2-binary (installed)

---

## 🔑 Important Credentials

### Airflow
- URL: http://localhost:8089
- Username: `admin`
- Password: `admin`

### Superset
- URL: http://localhost:8088
- Username: `admin`
- Password: `admin`

### MinIO
- Console: http://localhost:9001
- Username: `minio`
- Password: `minio12345`

### PostgreSQL
- Host: postgres:5432
- Database: `lakehouse`
- Username: `airflow`
- Password: `airflow`

---

## 🎯 Service URLs

| Service | URL | Status |
|---------|-----|--------|
| Spark Master (Streaming) | http://localhost:8080 | ✅ Running |
| Spark Master (Batch) | http://localhost:8083 | ✅ Running |
| Airflow | http://localhost:8089 | ✅ Running |
| Superset | http://localhost:8088 | ✅ Running |
| MinIO Console | http://localhost:9001 | ✅ Running |

---

## 📝 Backup Instructions

### Option 1: Git Clone (Recommended)
```bash
git clone https://github.com/vcvegeta/tesla-telemetry-lakehouse.git
```

### Option 2: Manual Backup
Copy the entire `tesla-telemetry-lakehouse` folder to your backup location:
```bash
cp -r /Users/viraatchaudhary/projects/tesla-telemetry-lakehouse ~/Desktop/backup/
```

### Option 3: Compressed Archive
```bash
cd /Users/viraatchaudhary/projects
tar -czf tesla-lakehouse-backup-2026-01-17.tar.gz tesla-telemetry-lakehouse/
```

---

## ✅ Verification Commands

### Check Git Status
```bash
cd /Users/viraatchaudhary/projects/tesla-telemetry-lakehouse
git status
# Should show: "nothing to commit, working tree clean"
```

### Verify All Files Committed
```bash
git log --oneline -1
# Should show: "Initial commit: Tesla Telemetry Lakehouse"
```

### Count Project Files
```bash
find . -type f | grep -v ".git" | wc -l
# Should show: 19+ files
```

### Verify Docker Images
```bash
docker images | grep viraat
# Should show 3 images: spark, airflow, ingestor
```

---

## 🎓 What This Project Demonstrates

- ✅ **Stream Processing**: Kafka + Spark Structured Streaming
- ✅ **Batch Processing**: Airflow orchestration
- ✅ **Data Architecture**: Medallion (Bronze/Silver/Gold) pattern
- ✅ **Data Lake**: MinIO (S3-compatible storage)
- ✅ **Data Warehouse**: PostgreSQL for analytical queries
- ✅ **Visualization**: Apache Superset dashboards
- ✅ **DevOps**: Docker containerization and Docker Hub publishing
- ✅ **Version Control**: Git with comprehensive documentation

---

## 🚀 Deployment

### For Recruiters/Others
```bash
git clone https://github.com/vcvegeta/tesla-telemetry-lakehouse.git
cd tesla-telemetry-lakehouse
docker-compose up -d
```

### For Your Backup Restoration
```bash
# Restore from backup
cp -r ~/Desktop/backup/tesla-telemetry-lakehouse ~/projects/

# Or use Git
cd ~/projects
git clone https://github.com/vcvegeta/tesla-telemetry-lakehouse.git
```

---

## 📊 Current System State

**Date**: January 17, 2026  
**All Services**: Running (13 containers healthy)  
**Streaming Jobs**: Active (2 jobs running)  
**Batch Job**: Scheduled every 10 minutes via Airflow  
**PostgreSQL Data**: 496 vehicle metrics records  
**Superset Dashboards**: 2 charts with 10-min auto-refresh  
**Memory Usage**: ~6.8GB / 7.5GB (91%)  
**Git Status**: Clean (all committed and pushed)  
**Docker Hub**: All 3 images published  

---

**✅ ALL FILES SAVED AND BACKED UP SUCCESSFULLY!**

You can now safely backup this entire folder to any location on your Mac.
