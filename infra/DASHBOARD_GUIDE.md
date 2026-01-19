# 📊 Dashboard Creation Guide

This guide shows you how to create custom dashboards and charts in Superset to visualize your Tesla fleet data.

---

## 🎉 What's Already Automated For You

**Good news!** We've automated the tedious setup so you can focus on creating great visualizations:

✅ **PostgreSQL Database Connection** - Already configured and ready to use  
✅ **Superset Initialization** - Admin user created (username: `admin`, password: `admin`)  
✅ **PostgreSQL Driver** - Pre-installed for seamless database connectivity  
✅ **MinIO Object Storage** - Buckets auto-created for data lake  
✅ **Database Tables** - Gold layer tables (`gold_vehicle_minute_metrics`, `gold_fleet_minute_metrics`) ready with data

**All you need to do:** Create your charts! (~5 minutes)

---

## ✅ Prerequisites

1. Wait 10-15 minutes after starting containers for data to accumulate
2. Verify data exists:
   ```bash
   docker exec tesla-telemetry-postgres-1 psql -U airflow -d lakehouse -c "SELECT COUNT(*) FROM gold_vehicle_minute_metrics;"
   ```
   Should show > 0 records

---

## 🚀 Quick Start: Create Your First Dashboard

### Step 1: Access Superset & Verify Database Connection

1. Open Superset: **http://localhost:8088**
2. Login with:
   - **Username:** `admin`
   - **Password:** `admin`
3. Click **Settings (⚙️)** → **Database Connections**
4. You should see **"Tesla Lakehouse"** already created! ✅
   - If you want to test it, click on it and click **"Test Connection"**
   - Connection string: `postgresql+psycopg2://airflow:airflow@postgres:5432/lakehouse`

---

### Step 2: Create Dataset

1. Click **Data** → **Datasets**
2. Click **+ Dataset**
3. Fill in:
   - **Database:** Tesla Lakehouse
   - **Schema:** public
   - **Table:** gold_vehicle_minute_metrics
4. Click **Create Dataset and Create Chart**

**Available Columns in `gold_vehicle_minute_metrics`:**

![gold_vehicle_minute_metrics columns](../docs/images/gold_vehicle_minute_metrics_columns.png)

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `vehicle_id` | TEXT | Unique identifier for each vehicle |
| `minute_ts` | TIMESTAMP | Timestamp for minute-level aggregation |
| `avg_speed_mph` | DOUBLE PRECISION | Average speed in miles per hour |
| `max_speed_mph` | DOUBLE PRECISION | Maximum speed in miles per hour |
| `min_battery_percent` | INTEGER | Minimum battery percentage |
| `event_count` | BIGINT | Total number of telemetry events |

---

### Step 3: Create Chart 1 - Battery Level Over Time (Line Chart)

Now let's create your first visualization!

1. After creating the dataset, you'll automatically be in the chart builder
2. **Select Visualization Type:** Click on visualization type dropdown and select **"Line Chart"** (or **"Time-series Line Chart"**)

**Configure the chart:**
- **TIME:**
  - X-Axis (Time Column): `minute_ts`
  - Time Grain: `Minute` (or leave as default)
  
- **QUERY:**
  - Metrics: Click **"+ ADD METRIC"**
    - Choose **Simple** tab
    - Column: `min_battery_percent`
    - Aggregate: `MIN`
    - Label: `MIN(min_battery_percent)` (auto-generated)
  
- **CUSTOMIZE** (Optional):
  - Chart Title: `Tesla Battery Level Over Time`
  - X Axis Label: `Time`
  - Y Axis Label: `Battery Level (%)`

3. Click **"UPDATE CHART"** or **"RUN"** to preview your visualization
4. Once satisfied, click **"SAVE"**
   - Chart Name: `Tesla Battery Level Over Time`
   - **Check** "Add to dashboard"
   - Dashboard: Select **"[Create new dashboard]"**
   - Dashboard Name: `Tesla Fleet Dashboard`
5. Click **"SAVE & GO TO DASHBOARD"**

🎉 **Your first chart is live!**

---

### Step 4: Create Chart 2 - Events Per Minute (Bar Chart)

Let's add a second chart to track telemetry event volume!

1. Go to **Data** → **Datasets**
2. Find `gold_vehicle_minute_metrics` and click on it
3. Click **"CREATE CHART"** button
4. **Select Visualization Type:** Choose **"Bar Chart"** (or **"Time-series Bar Chart"**)

**Configure the chart:**
- **TIME:**
  - X-Axis (Time Column): `minute_ts`
  - Time Grain: `Minute`
  
- **QUERY:**
  - Metrics: Click **"+ ADD METRIC"**
    - Choose **Simple** tab
    - Column: `event_count`
    - Aggregate: `SUM`
    - Label: `SUM(event_count)` (auto-generated)
  
- **CUSTOMIZE** (Optional):
  - Chart Title: `Tesla Telemetry Events Per Minute`
  - X Axis Label: `Time`
  - Y Axis Label: `Event Count`

3. Click **"UPDATE CHART"** or **"RUN"** to preview
4. Click **"SAVE"**
   - Chart Name: `Tesla Telemetry Events Per Minute`
   - **Check** "Add to dashboard"
   - Dashboard: Select `Tesla Fleet Dashboard` (the one you just created)
5. Click **"SAVE & GO TO DASHBOARD"**

🎊 **You now have 2 live charts on your dashboard!**

---

### Step 5: Arrange & Enable Auto-Refresh (Optional)

1. In your **Tesla Fleet Dashboard**, click **"EDIT DASHBOARD"** (pencil icon)
2. Drag and arrange your charts as you like
3. To enable auto-refresh:
   - Click **⋮** (three dots menu) → **"Settings"**
   - Enable **"AUTO REFRESH"**
   - Set interval: `10 seconds` or `1 minute` (for real-time updates)
   - Click **"SAVE"**
4. Click **"SAVE"** to save your dashboard layout

---

## 🎨 Example Dashboards You Can Create

Here are some chart ideas using the available data:

### Available Tables:
1. **`gold_vehicle_minute_metrics`**
   - Columns: `vehicle_id`, `minute_ts`, `avg_speed_mph`, `max_speed_mph`, `min_battery_percent`, `event_count`
   - See column details in Step 2 above

2. **`gold_fleet_minute_metrics`**
   - Columns: `minute_ts`, `avg_speed_mph_fleet`, `min_battery_percent_fleet`, `total_events`

![gold_fleet_minute_metrics columns](../docs/images/gold_fleet_minute_metrics_columns.png)

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `minute_ts` | TIMESTAMP | Timestamp for minute-level aggregation |
| `avg_speed_mph_fleet` | DOUBLE PRECISION | Fleet-wide average speed |
| `min_battery_percent_fleet` | INTEGER | Fleet-wide minimum battery percentage |
| `total_events` | BIGINT | Total events across all vehicles |

---

### Chart Ideas:
- 📈 **Line Chart:** Average Speed Over Time (`avg_speed_mph`)
- 📊 **Bar Chart:** Maximum Speed Per Minute (`max_speed_mph`)
- 🔋 **Area Chart:** Battery Level Trend (`min_battery_percent`)
- 📉 **Line Chart:** Fleet-wide Average Speed (`avg_speed_mph_fleet`)
- 🎯 **Big Number:** Total Events (use `SUM(total_events)`)
- 📊 **Table:** Latest Metrics per Vehicle

**Pro Tip:** You can create as many charts and dashboards as you want! Superset supports 50+ visualization types.

---

## 📸 Sample Dashboard Preview

Below is an example of what your Tesla Fleet Dashboard looks like with the 2 example charts:

![Tesla Fleet Dashboard](../docs/images/tesla_fleet_dashboard.png)

**Tesla Fleet Dashboard:**
- **Chart 1 (Left):** Battery Level Over Time (Line Chart)
  - Metric: `MIN(min_battery_percent)` 
  - Shows battery level trending over time
  - Helps identify battery drain patterns
  - Time range: Real-time telemetry data
  
- **Chart 2 (Right):** Events Per Minute (Bar Chart)
  - Metric: `SUM(event_count)`
  - Tracks telemetry event volume per minute
  - Useful for monitoring data ingestion health
  - Shows consistent event flow through the pipeline

*This dashboard was created in ~5 minutes following the steps above. Your charts will populate with real data after ~15 minutes of the system running.*

---

## ✅ Verification

After creating your dashboard, verify everything works:

1. **Check Data Appears:** Charts should display data (may be empty initially)
2. **Auto-Refresh Works:** If enabled, dashboard updates automatically
3. **Multiple Vehicles:** If you have multiple vehicle IDs, you can add filters
4. **Time Range:** Use Superset's time range selector to zoom in/out

---

## 🎯 What's Automated vs Manual

### ✅ Automated (Zero Setup Required):
- PostgreSQL database connection to `lakehouse`
- Superset initialization with admin user
- PostgreSQL driver installation
- MinIO buckets and data lake structure
- Gold layer tables with aggregated metrics
- Data pipeline (Kafka → MinIO → Spark → PostgreSQL)

### 👤 Manual (Your Creative Control - ~5 minutes):
- Creating datasets from tables
- Building custom charts and visualizations
- Designing dashboard layouts
- Setting refresh intervals
- Adding filters and drill-downs

**Why manual?** This gives you full flexibility to create exactly the visualizations you need for your use case!

---

## 💾 Export Your Dashboards (Optional)

Want to share your dashboard configuration?

```bash
cd /Users/viraatchaudhary/projects/tesla-telemetry-lakehouse/infra
docker exec tesla-telemetry-superset-1 superset export-dashboards -f /tmp/my_dashboards.zip
docker cp tesla-telemetry-superset-1:/tmp/my_dashboards.zip ./superset/my_dashboards_export.zip
```

This creates a portable dashboard configuration you can import into other Superset instances.

---

## 📝 Troubleshooting

**No data in charts?**
- Wait 15-20 minutes for initial data to flow through the pipeline
- Check if data exists: `docker exec tesla-telemetry-postgres-1 psql -U airflow -d lakehouse -c "SELECT COUNT(*) FROM gold_vehicle_minute_metrics;"`

**Database connection not found?**
- Restart Superset: `docker-compose restart superset`
- The connection should auto-create on startup

**Charts not saving?**
- Ensure you're logged in as admin
- Check Superset logs: `docker logs tesla-telemetry-superset-1`

---

## 🚀 You're All Set!

You now have a fully automated Tesla telemetry data lakehouse with custom dashboards. The hard infrastructure work is done - now focus on building insightful visualizations!

**Happy Dashboarding! 📊✨**
