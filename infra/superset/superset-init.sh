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

# Create database connection programmatically
echo "🔗 Creating PostgreSQL database connection..."
python << 'PYEOF'
from superset import app, db
from superset.models.core import Database
import logging

logging.basicConfig(level=logging.INFO)

with app.app_context():
    # Check if database already exists
    existing_db = db.session.query(Database).filter_by(database_name='Tesla Lakehouse').first()
    
    if not existing_db:
        # Create new database connection
        new_db = Database(
            database_name='Tesla Lakehouse',
            sqlalchemy_uri='postgresql+psycopg2://airflow:airflow@postgres:5432/lakehouse',
            expose_in_sqllab=True,
            allow_ctas=True,
            allow_cvas=True,
            allow_dml=True,
        )
        db.session.add(new_db)
        db.session.commit()
        print("✅ Database connection 'Tesla Lakehouse' created successfully!")
    else:
        print("ℹ️  Database connection 'Tesla Lakehouse' already exists")
PYEOF

# Import dashboards if export file exists
if [ -f "/app/docker/dashboards_export.zip" ]; then
    echo "📊 Importing dashboards..."
    superset import-dashboards -p /app/docker/dashboards_export.zip -u admin || echo "⚠️  Dashboard import failed - will be available after first database connection"
else
    echo "ℹ️  No dashboard export found, skipping import"
fi

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
