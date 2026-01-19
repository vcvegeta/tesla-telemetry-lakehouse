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

# Create database connection only - charts will be created via UI using DASHBOARD_GUIDE.md
echo "🔗 Creating PostgreSQL database connection..."
python << 'PYEOF'
import sqlite3

conn = sqlite3.connect('/app/superset_home/superset.db')
cursor = conn.cursor()

# Create database connection
cursor.execute("SELECT id FROM dbs WHERE database_name = 'Tesla Lakehouse'")
db_row = cursor.fetchone()

if not db_row:
    cursor.execute("""
        INSERT INTO dbs (database_name, sqlalchemy_uri, expose_in_sqllab, allow_ctas, allow_cvas, allow_dml, created_on, changed_on)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, ('Tesla Lakehouse', 'postgresql+psycopg2://airflow:airflow@postgres:5432/lakehouse', 1, 1, 1, 1))
    conn.commit()
    print("✅ Database connection 'Tesla Lakehouse' created successfully!")
else:
    print("ℹ️  Database connection 'Tesla Lakehouse' already exists")

conn.close()
PYEOF

echo "✅ Superset initialization complete!"
echo "📊 Follow DASHBOARD_GUIDE.md to create your charts (takes 5 minutes)"

# Start Superset
echo "🚀 Starting Superset server..."
exec gunicorn \
    -b 0.0.0.0:8088 \
    --workers 2 \
    --timeout 300 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    "superset.app:create_app()"
