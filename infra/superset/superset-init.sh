#!/bin/bash
set -e

echo "🔧 Initializing Superset..."

# Install PostgreSQL driver
echo "📦 Installing psycopg2-binary..."
pip install psycopg2-binary

# Initialize database
echo "🗄️  Upgrading Superset database..."
superset db upgrade

# Create admin user (only if doesn't exist)
echo "👤 Creating admin user..."
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@superset.com \
    --password admin || echo "Admin user already exists"

# Initialize Superset
echo "⚙️  Initializing Superset..."
superset init

# Create database connection, dataset, charts and dashboard via direct SQLite
echo "🔗 Creating database connection, dataset, charts and dashboard..."
python << 'PYEOF'
import sqlite3
import json
import uuid
from datetime import datetime

conn = sqlite3.connect('/app/superset_home/superset.db')
cursor = conn.cursor()

# 1. Create database connection
cursor.execute("SELECT id FROM dbs WHERE database_name = 'Tesla Lakehouse'")
db_row = cursor.fetchone()

if not db_row:
    cursor.execute("""
        INSERT INTO dbs (database_name, sqlalchemy_uri, expose_in_sqllab, allow_ctas, allow_cvas, allow_dml, created_on, changed_on)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, ('Tesla Lakehouse', 'postgresql+psycopg2://airflow:airflow@postgres:5432/lakehouse', 1, 1, 1, 1))
    conn.commit()
    cursor.execute("SELECT id FROM dbs WHERE database_name = 'Tesla Lakehouse'")
    db_row = cursor.fetchone()
    print("✅ Database connection created")
else:
    print("ℹ️  Database connection already exists")

db_id = db_row[0]

# 2. Create dataset (table)
cursor.execute("SELECT id FROM tables WHERE table_name = 'gold_vehicle_minute_metrics' AND database_id = ?", (db_id,))
table_row = cursor.fetchone()

if not table_row:
    table_uuid = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO tables (table_name, main_dttm_col, database_id, schema, sql, is_managed_externally, external_url, created_on, changed_on, uuid)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
    """, ('gold_vehicle_minute_metrics', 'minute_ts', db_id, 'public', None, 0, None, table_uuid))
    conn.commit()
    cursor.execute("SELECT id FROM tables WHERE table_name = 'gold_vehicle_minute_metrics' AND database_id = ?", (db_id,))
    table_row = cursor.fetchone()
    print("✅ Dataset created")
else:
    print("ℹ️  Dataset already exists")

table_id = table_row[0]

# 3. Create Chart 1 - Battery Level
cursor.execute("SELECT id FROM slices WHERE slice_name = 'Tesla Battery Level Over Time'")
if not cursor.fetchone():
    chart1_params = json.dumps({
        "viz_type": "echarts_timeseries_line",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "min_battery_percent"}, "aggregate": "MIN", "label": "MIN(min_battery_percent)"}],
        "groupby": [],
        "x_axis": "minute_ts",
        "time_grain_sqla": "PT1M",
        "adhoc_filters": [],
        "row_limit": 10000
    })
    
    chart1_uuid = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO slices (slice_name, datasource_type, datasource_id, viz_type, params, created_on, changed_on, uuid)
        VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
    """, ('Tesla Battery Level Over Time', 'table', table_id, 'echarts_timeseries_line', chart1_params, chart1_uuid))
    conn.commit()
    print("✅ Battery Level chart created")
else:
    print("ℹ️  Battery Level chart already exists")

# 4. Create Chart 2 - Events
cursor.execute("SELECT id FROM slices WHERE slice_name = 'Tesla Telemetry Events Per Minute'")
if not cursor.fetchone():
    chart2_params = json.dumps({
        "viz_type": "echarts_timeseries_bar",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "event_count"}, "aggregate": "SUM", "label": "SUM(event_count)"}],
        "groupby": [],
        "x_axis": "minute_ts",
        "time_grain_sqla": "PT1M",
        "adhoc_filters": [],
        "row_limit": 10000
    })
    
    chart2_uuid = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO slices (slice_name, datasource_type, datasource_id, viz_type, params, created_on, changed_on, uuid)
        VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
    """, ('Tesla Telemetry Events Per Minute', 'table', table_id, 'echarts_timeseries_bar', chart2_params, chart2_uuid))
    conn.commit()
    print("✅ Events chart created")
else:
    print("ℹ️  Events chart already exists")

# 5. Create Dashboard
cursor.execute("SELECT id FROM dashboards WHERE dashboard_title = 'Tesla Fleet Dashboard'")
dash_row = cursor.fetchone()

if not dash_row:
    dash_uuid = str(uuid.uuid4())
    position_json = json.dumps({})
    cursor.execute("""
        INSERT INTO dashboards (dashboard_title, position_json, created_on, changed_on, uuid)
        VALUES (?, ?, datetime('now'), datetime('now'), ?)
    """, ('Tesla Fleet Dashboard', position_json, dash_uuid))
    conn.commit()
    
    # Link charts to dashboard
    cursor.execute("SELECT id FROM dashboards WHERE dashboard_title = 'Tesla Fleet Dashboard'")
    dash_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM slices WHERE slice_name = 'Tesla Battery Level Over Time'")
    chart1_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM slices WHERE slice_name = 'Tesla Telemetry Events Per Minute'")
    chart2_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO dashboard_slices (dashboard_id, slice_id) VALUES (?, ?)", (dash_id, chart1_id))
    cursor.execute("INSERT INTO dashboard_slices (dashboard_id, slice_id) VALUES (?, ?)", (dash_id, chart2_id))
    conn.commit()
    print("✅ Dashboard created with both charts")
else:
    print("ℹ️  Dashboard already exists")

conn.close()
print("✅ All database, dataset, charts and dashboard created!")
PYEOF

echo "✅ Superset initialization complete!"

# Start Superset
echo "🚀 Starting Superset server..."
exec gunicorn \
    -b 0.0.0.0:8088 \
    --workers 2 \
    --timeout 300 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    "superset.app:create_app()"
