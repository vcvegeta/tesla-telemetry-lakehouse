#!/usr/bin/env python3
"""
Script to programmatically create Tesla Fleet Dashboard with charts in Superset.
This runs within the Superset container to create datasets and charts.
"""
import sqlite3
import json
from datetime import datetime

# Connect to Superset metadata database
conn = sqlite3.connect('/app/superset_home/superset.db')
cursor = conn.cursor()

# Get the database ID for Tesla Lakehouse
cursor.execute("SELECT id FROM dbs WHERE database_name = 'Tesla Lakehouse'")
db_result = cursor.fetchone()
if not db_result:
    print("❌ Tesla Lakehouse database connection not found!")
    exit(1)

db_id = db_result[0]
print(f"✅ Found Tesla Lakehouse database (ID: {db_id})")

# Create datasets (tables) for the charts with explicit column definitions
datasets = [
    {
        'table_name': 'gold_vehicle_minute_metrics',
        'schema': 'public',
        'description': 'Vehicle metrics aggregated per minute',
        'columns': [
            {'column_name': 'vehicle_id', 'type': 'TEXT', 'is_dttm': False},
            {'column_name': 'minute_ts', 'type': 'TIMESTAMP', 'is_dttm': True},
            {'column_name': 'avg_speed_mph', 'type': 'DOUBLE PRECISION', 'is_dttm': False},
            {'column_name': 'max_speed_mph', 'type': 'DOUBLE PRECISION', 'is_dttm': False},
            {'column_name': 'min_battery_percent', 'type': 'INTEGER', 'is_dttm': False},
            {'column_name': 'event_count', 'type': 'BIGINT', 'is_dttm': False},
        ]
    },
    {
        'table_name': 'gold_fleet_minute_metrics',
        'schema': 'public',
        'description': 'Fleet-wide metrics aggregated per minute',
        'columns': [
            {'column_name': 'minute_ts', 'type': 'TIMESTAMP', 'is_dttm': True},
            {'column_name': 'avg_speed_mph_fleet', 'type': 'DOUBLE PRECISION', 'is_dttm': False},
            {'column_name': 'min_battery_percent_fleet', 'type': 'INTEGER', 'is_dttm': False},
            {'column_name': 'total_events', 'type': 'BIGINT', 'is_dttm': False},
        ]
    }
]

dataset_ids = {}
for dataset in datasets:
    # Check if dataset already exists
    cursor.execute("""
        SELECT id FROM tables 
        WHERE table_name = ? AND database_id = ?
    """, (dataset['table_name'], db_id))
    
    existing = cursor.fetchone()
    if existing:
        dataset_ids[dataset['table_name']] = existing[0]
        print(f"ℹ️  Dataset '{dataset['table_name']}' already exists (ID: {existing[0]})")
    else:
        # Insert new dataset
        cursor.execute("""
            INSERT INTO tables (database_id, table_name, schema, description, created_on, changed_on)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (db_id, dataset['table_name'], dataset['schema'], dataset['description']))
        
        dataset_id = cursor.lastrowid
        dataset_ids[dataset['table_name']] = dataset_id
        print(f"✅ Created dataset '{dataset['table_name']}' (ID: {dataset_id})")
        
        # Insert columns for the dataset
        for col in dataset['columns']:
            cursor.execute("""
                INSERT INTO table_columns (table_id, column_name, type, is_dttm, created_on, changed_on)
                VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (dataset_id, col['column_name'], col['type'], 1 if col['is_dttm'] else 0))
        
        print(f"  ↳ Added {len(dataset['columns'])} columns")

conn.commit()

# Create charts
charts = [
    {
        'slice_name': 'Battery Level Over Time',
        'viz_type': 'echarts_timeseries_line',
        'datasource_id': dataset_ids['gold_vehicle_minute_metrics'],
        'datasource_type': 'table',
        'params': json.dumps({
            'time_grain_sqla': 'P1M',
            'time_range': 'No filter',
            'metrics': [{'expressionType': 'SIMPLE', 'column': {'column_name': 'min_battery_percent'}, 'aggregate': 'AVG', 'label': 'AVG(min_battery_percent)'}],
            'adhoc_filters': [],
            'groupby': [],
            'viz_type': 'echarts_timeseries_line',
        })
    },
    {
        'slice_name': 'Events Per Minute',
        'viz_type': 'echarts_timeseries_bar',
        'datasource_id': dataset_ids['gold_fleet_minute_metrics'],
        'datasource_type': 'table',
        'params': json.dumps({
            'time_grain_sqla': 'P1M',
            'time_range': 'No filter',
            'metrics': [{'expressionType': 'SIMPLE', 'column': {'column_name': 'total_events'}, 'aggregate': 'SUM', 'label': 'SUM(total_events)'}],
            'adhoc_filters': [],
            'groupby': [],
            'viz_type': 'echarts_timeseries_bar',
        })
    }
]

chart_ids = []
for chart in charts:
    # Check if chart already exists
    cursor.execute("""
        SELECT id FROM slices 
        WHERE slice_name = ? AND datasource_id = ?
    """, (chart['slice_name'], chart['datasource_id']))
    
    existing = cursor.fetchone()
    if existing:
        chart_ids.append(existing[0])
        print(f"ℹ️  Chart '{chart['slice_name']}' already exists (ID: {existing[0]})")
    else:
        # Insert new chart
        cursor.execute("""
            INSERT INTO slices (slice_name, datasource_type, datasource_id, viz_type, params, created_on, changed_on)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (chart['slice_name'], chart['datasource_type'], chart['datasource_id'], 
              chart['viz_type'], chart['params']))
        
        chart_ids.append(cursor.lastrowid)
        print(f"✅ Created chart '{chart['slice_name']}' (ID: {cursor.lastrowid})")

conn.commit()

# Create dashboard
dashboard_title = 'Tesla Fleet Dashboard'
cursor.execute("""
    SELECT id FROM dashboards 
    WHERE dashboard_title = ?
""", (dashboard_title,))

existing_dashboard = cursor.fetchone()
if existing_dashboard:
    dashboard_id = existing_dashboard[0]
    print(f"ℹ️  Dashboard '{dashboard_title}' already exists (ID: {dashboard_id})")
else:
    # Create dashboard
    position_json = json.dumps({
        "DASHBOARD_VERSION_KEY": "v2",
        "GRID_ID": {
            "type": "GRID",
            "id": "GRID_ID",
            "children": [f"CHART-{chart_ids[0]}", f"CHART-{chart_ids[1]}"],
            "parents": ["ROOT_ID"]
        },
        f"CHART-{chart_ids[0]}": {
            "type": "CHART",
            "id": f"CHART-{chart_ids[0]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {
                "width": 6,
                "height": 50,
                "chartId": chart_ids[0]
            }
        },
        f"CHART-{chart_ids[1]}": {
            "type": "CHART",
            "id": f"CHART-{chart_ids[1]}",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {
                "width": 6,
                "height": 50,
                "chartId": chart_ids[1]
            }
        }
    })
    
    cursor.execute("""
        INSERT INTO dashboards (dashboard_title, position_json, created_on, changed_on, published)
        VALUES (?, ?, datetime('now'), datetime('now'), 1)
    """, (dashboard_title, position_json))
    
    dashboard_id = cursor.lastrowid
    print(f"✅ Created dashboard '{dashboard_title}' (ID: {dashboard_id})")
    
    # Link charts to dashboard
    for chart_id in chart_ids:
        cursor.execute("""
            INSERT INTO dashboard_slices (dashboard_id, slice_id)
            VALUES (?, ?)
        """, (dashboard_id, chart_id))
    
    print(f"✅ Linked {len(chart_ids)} charts to dashboard")

conn.commit()
conn.close()

print("\n🎉 Tesla Fleet Dashboard setup complete!")
print(f"   - Database: Tesla Lakehouse")
print(f"   - Datasets: {len(datasets)}")
print(f"   - Charts: {len(charts)}")
print(f"   - Dashboard: {dashboard_title}")
print(f"\n🌐 Access at: http://localhost:8088 (admin/admin)")
