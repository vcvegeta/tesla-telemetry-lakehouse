#!/bin/bash
set -e

echo "🔧 Initializing Tesla Lakehouse Database..."

# Create lakehouse database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE lakehouse'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lakehouse')\gexec
EOSQL

# Create tables in lakehouse database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=lakehouse <<-EOSQL
    CREATE TABLE IF NOT EXISTS gold_vehicle_minute_metrics (
        vin VARCHAR(50),
        window_start TIMESTAMP,
        window_end TIMESTAMP,
        avg_battery_level DOUBLE PRECISION,
        avg_speed DOUBLE PRECISION,
        total_events BIGINT
    );

    CREATE TABLE IF NOT EXISTS gold_fleet_minute_metrics (
        window_start TIMESTAMP,
        window_end TIMESTAMP,
        total_vehicles BIGINT,
        avg_battery_level DOUBLE PRECISION,
        avg_speed DOUBLE PRECISION,
        total_events BIGINT
    );

    -- Create indexes for better query performance
    CREATE INDEX IF NOT EXISTS idx_vehicle_window_start ON gold_vehicle_minute_metrics(window_start);
    CREATE INDEX IF NOT EXISTS idx_fleet_window_start ON gold_fleet_minute_metrics(window_start);
EOSQL

echo "✅ Lakehouse database and tables created successfully!"
