#!/bin/bash
# Script to export Superset dashboards for automatic import

set -e

echo "📊 Exporting Superset dashboards..."

# Wait for Superset to be ready
sleep 5

# Export all dashboards
docker exec tesla-telemetry-superset-1 superset export-dashboards -f /tmp/dashboards.zip

# Copy to host
docker cp tesla-telemetry-superset-1:/tmp/dashboards.zip ./superset/dashboards_export.zip

echo "✅ Dashboards exported to ./superset/dashboards_export.zip"
echo ""
echo "💡 This file will be automatically imported on Superset startup!"
