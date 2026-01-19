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

# Import dashboards if export file exists
if [ -f "/app/docker/dashboards_export.zip" ]; then
    echo "📊 Importing dashboards..."
    superset import-dashboards -p /app/docker/dashboards_export.zip -u admin || echo "⚠️  Dashboard import failed (might be first run)"
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
