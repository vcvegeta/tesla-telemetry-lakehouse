# Tesla Fleet Dashboard - Auto-Initialized Superset Setup

## Overview

This deployment includes a **fully automated** Superset dashboard that requires **ZERO manual configuration**. Everything is programmatically created during the first startup.

## What Gets Auto-Created

### ✅ Database Connection
- **Name**: Tesla Lakehouse
- **Type**: PostgreSQL
- **Connection**: `postgresql+psycopg2://airflow:airflow@postgres:5432/lakehouse`
- **Status**: Automatically created and tested on startup

### ✅ Datasets (Tables)
1. **gold_vehicle_minute_metrics**
   - Vehicle-level metrics aggregated per minute
   - Fields: VIN, window_start, window_end, avg_battery_level, avg_speed, total_events

2. **gold_fleet_minute_metrics**
   - Fleet-wide metrics aggregated per minute
   - Fields: window_start, window_end, total_vehicles, avg_battery_level, avg_speed, total_events

### ✅ Charts
1. **Battery Level Over Time**
   - Type: Line Chart (ECharts Time Series)
   - Dataset: gold_vehicle_minute_metrics
   - Metric: avg_battery_level
   - Time Column: window_start

2. **Events Per Minute**
   - Type: Bar Chart (ECharts Time Series)
   - Dataset: gold_fleet_minute_metrics
   - Metric: total_events
   - Time Column: window_start

### ✅ Dashboard
- **Name**: Tesla Fleet Dashboard
- **Charts**: 2 charts (Battery Level Over Time, Events Per Minute)
- **Layout**: Side-by-side grid layout
- **Status**: Published and ready to view

## Access Information

### Superset Web UI
- **URL**: http://localhost:8088
- **Username**: `admin`
- **Password**: `admin`

### Direct Dashboard Access
After logging in, navigate to:
- **Dashboards** → **Tesla Fleet Dashboard**

Or use the direct URL (after logging in):
- http://localhost:8088/superset/dashboard/1/

## First-Time Startup

When you run `docker-compose up -d` for the first time, the system will:

1. ✅ Initialize Superset database
2. ✅ Create admin user (admin/admin)
3. ✅ Install PostgreSQL driver (psycopg2-binary)
4. ✅ Create "Tesla Lakehouse" database connection
5. ✅ Create datasets for gold tables
6. ✅ Create 2 charts (Battery Level, Events Per Minute)
7. ✅ Create "Tesla Fleet Dashboard" with charts
8. ✅ Start Superset web server

**Total Time**: ~60 seconds for complete initialization

## Data Flow Timeline

After startup, data flows through the pipeline:

| Time | Event |
|------|-------|
| **0 min** | Services start, Superset initialization complete |
| **1-2 min** | MinIO bucket created, PostgreSQL tables created |
| **2-5 min** | Ingestor generates mock Tesla events → Kafka |
| **5-10 min** | Streaming job processes Bronze → Silver (Parquet in MinIO) |
| **10-15 min** | Batch job aggregates Silver → Gold (PostgreSQL tables) |
| **15+ min** | **Charts populate with data** 🎉 |

## Verification Steps

### 1. Check Superset is Running
```bash
docker logs tesla-telemetry-superset-1 | grep "initialization complete"
# Expected: "✅ Superset initialization complete!"
```

### 2. Verify Database Connection Created
```bash
docker exec tesla-telemetry-superset-1 python -c "import sqlite3; conn = sqlite3.connect('/app/superset_home/superset.db'); cursor = conn.cursor(); cursor.execute('SELECT database_name, sqlalchemy_uri FROM dbs'); print(cursor.fetchall())"
# Expected: [('Tesla Lakehouse', 'postgresql+psycopg2://airflow:airflow@postgres:5432/lakehouse')]
```

### 3. Verify Charts Created
```bash
docker exec tesla-telemetry-superset-1 python -c "import sqlite3; conn = sqlite3.connect('/app/superset_home/superset.db'); cursor = conn.cursor(); cursor.execute('SELECT slice_name FROM slices'); print(cursor.fetchall())"
# Expected: [('Battery Level Over Time',), ('Events Per Minute',)]
```

### 4. Verify Dashboard Created
```bash
docker exec tesla-telemetry-superset-1 python -c "import sqlite3; conn = sqlite3.connect('/app/superset_home/superset.db'); cursor = conn.cursor(); cursor.execute('SELECT dashboard_title FROM dashboards'); print(cursor.fetchall())"
# Expected: [('Tesla Fleet Dashboard',)]
```

### 5. Check Data in Gold Tables
```bash
docker exec tesla-telemetry-postgres-1 psql -U airflow -d lakehouse -c "SELECT COUNT(*) FROM gold_vehicle_minute_metrics;"
# Expected: > 0 (after 10-15 minutes of runtime)
```

## Testing Full Automation

To verify **complete automation** from scratch:

```bash
# Stop and delete ALL volumes (nuclear option)
cd infra
docker-compose down -v

# Start fresh (zero manual steps required)
docker-compose up -d

# Wait 60 seconds for Superset initialization
sleep 60

# Login and view dashboard
# http://localhost:8088 (admin/admin)
# Navigate to "Tesla Fleet Dashboard"

# Wait 10-15 minutes for data to populate charts
```

## Architecture

### Initialization Flow
```
┌─────────────────────────────────────────────────────────────┐
│ Superset Container Startup                                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ superset-init.sh (Entrypoint Script)                       │
│ ├── Install psycopg2-binary                                │
│ ├── superset db upgrade                                    │
│ ├── Create admin user (admin/admin)                        │
│ ├── superset init                                          │
│ ├── Create PostgreSQL DB connection (SQLite insert)        │
│ ├── Run create_charts.py (programmatic chart creation)     │
│ └── Start gunicorn server                                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ create_charts.py (Python Script)                           │
│ ├── Create dataset: gold_vehicle_minute_metrics            │
│ ├── Create dataset: gold_fleet_minute_metrics              │
│ ├── Create chart: Battery Level Over Time                  │
│ ├── Create chart: Events Per Minute                        │
│ ├── Create dashboard: Tesla Fleet Dashboard                │
│ └── Link charts to dashboard                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Superset Ready at http://localhost:8088                    │
│ ✅ Database connection created                             │
│ ✅ Datasets configured                                     │
│ ✅ Charts created and linked                               │
│ ✅ Dashboard ready to view (charts populate when data flows)│
└─────────────────────────────────────────────────────────────┘
```

## Files Involved

### Docker Image Build
```
infra/superset/
├── Dockerfile                  # Builds custom Superset image
├── superset-init.sh           # Initialization script (entrypoint)
└── create_charts.py           # Programmatic chart creation
```

### Docker Compose
```
infra/docker-compose.yml
└── superset:
    └── image: viraat/tesla-telemetry-superset:latest
```

### Docker Hub Image
- **Repository**: https://hub.docker.com/r/viraat/tesla-telemetry-superset
- **Tag**: `latest`
- **Digest**: sha256:8878e01454eb4766f6b0c54cabdff09762f3ef4f16211ad00159449b33ed71d5

## Troubleshooting

### Charts Show "No Data"
**Cause**: Data hasn't flowed through the pipeline yet  
**Solution**: Wait 10-15 minutes after startup for the batch job to populate gold tables

### "Tesla Lakehouse" Connection Not Found
**Cause**: Initialization script didn't run  
**Solution**: Check logs with `docker logs tesla-telemetry-superset-1`

### Dashboard is Empty
**Cause**: Charts weren't created  
**Solution**: Check creation script ran: `docker logs tesla-telemetry-superset-1 | grep "setup complete"`

### Can't Login
**Credentials**: admin / admin (default)  
**Reset**: Run `docker-compose down -v && docker-compose up -d`

## Customization

### Modify Charts
Edit `infra/superset/create_charts.py`:
- Change metrics, time columns, or visualization types
- Add more charts to the charts array
- Rebuild image: `docker build -t viraat/tesla-telemetry-superset:latest -f superset/Dockerfile superset/`

### Add More Datasets
Edit `create_charts.py` datasets array:
```python
datasets = [
    {
        'table_name': 'your_table_name',
        'schema': 'public',
        'description': 'Your dataset description'
    }
]
```

### Modify Dashboard Layout
Edit the `position_json` in `create_charts.py` to change chart positioning and sizes

## Security Notes

### Default Credentials
⚠️ **WARNING**: Default admin credentials are `admin/admin`  
**Production**: Change password after first login or set via environment variables

### Database Password
The database connection includes the password in the SQLAlchemy URI  
**Production**: Use Superset's encrypted credentials feature

## Summary

This implementation achieves **100% automation** for Superset dashboard creation:
- ✅ Zero manual database connection setup
- ✅ Zero manual dataset configuration
- ✅ Zero manual chart creation
- ✅ Zero manual dashboard assembly
- ✅ Works perfectly after `docker-compose down -v` (complete volume deletion)

**User Experience**: Run `docker-compose up -d`, wait 60 seconds, open browser, login, see dashboard with charts that populate automatically as data flows.

**Perfect for**: Recruiters, demos, development, testing, and automated deployments where manual configuration is not acceptable.
