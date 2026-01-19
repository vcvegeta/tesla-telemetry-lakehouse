# 📊 Dashboard Creation Guide

Follow these steps to create the Tesla Fleet Dashboard with 2 charts.

---

## ✅ Prerequisites

1. Wait 10-15 minutes for data to accumulate in PostgreSQL
2. Check data exists:
   ```bash
   docker exec tesla-telemetry-postgres-1 psql -U airflow -d lakehouse -c "SELECT COUNT(*) FROM gold_vehicle_minute_metrics;"
   ```
   Should show > 0 records

---

## 🎯 Step 1: Connect to PostgreSQL Database

1. Open Superset: http://localhost:8088
2. Login: `admin` / `admin`
3. Click **Settings (⚙️)** → **Database Connections**
4. Click **+ Database**
5. Select **PostgreSQL**
6. Fill in:
   - **Display Name:** `Tesla Lakehouse`
   - **SQLAlchemy URI:** `postgresql+psycopg2://airflow:airflow@postgres:5432/lakehouse`
7. Click **Test Connection** → Should see "Connection successful!"
8. Click **Connect**

---

## 📈 Step 2: Create Dataset

1. Click **Data** → **Datasets**
2. Click **+ Dataset**
3. Fill in:
   - **Database:** Tesla Lakehouse
   - **Schema:** public
   - **Table:** gold_vehicle_minute_metrics
4. Click **Create Dataset and Create Chart**

---

## 📊 Step 3: Create Chart 1 - Battery Level Over Time

### Chart Configuration:
1. **Visualization Type:** Line Chart
2. **Time Column:** window_start
3. **Time Grain:** Minute
4. **Metrics:** avg_battery_level (AVG)
5. **X-Axis:** window_start
6. **Y-Axis:** avg_battery_level

### Detailed Steps:
1. In the chart builder:
   - **Query:**
     - Time Column: `window_start`
     - Time Grain: `Minute`
     - Metrics: Click "+ Add metric" → Select `AVG(avg_battery_level)`
   - **Chart Options:**
     - Title: `Tesla Battery Level Over Time`
     - X Axis Label: `Time`
     - Y Axis Label: `Battery Level (%)`
2. Click **Run** to preview
3. Click **Save** → Name: `Tesla Battery Level Chart`
4. Check "Add to dashboard"
5. Create new dashboard: `Tesla Fleet Dashboard`
6. Click **Save**

---

## 📊 Step 4: Create Chart 2 - Events Per Minute

1. Go back to **Data** → **Datasets** → Click `gold_vehicle_minute_metrics`
2. Click **Create Chart**
3. **Visualization Type:** Bar Chart

### Chart Configuration:
1. **Query:**
   - Time Column: `window_start`
   - Time Grain: `Minute`
   - Metrics: `SUM(total_events)`
2. **Chart Options:**
   - Title: `Tesla Telemetry Events Per Minute`
   - X Axis Label: `Time`
   - Y Axis Label: `Event Count`
3. Click **Run** to preview
4. Click **Save** → Name: `Tesla Events Per Minute Chart`
5. Add to dashboard: `Tesla Fleet Dashboard`
6. Click **Save**

---

## 🔄 Step 5: Enable Auto-Refresh

1. Go to **Dashboards** → Click `Tesla Fleet Dashboard`
2. Click **Edit Dashboard** (pencil icon)
3. Click **⋮** (three dots) → **Settings**
4. Enable **Auto Refresh**
5. Set interval: `10 minutes`
6. Click **Save**
7. Click **Save** again to save dashboard

---

## 💾 Step 6: Export Dashboards

After creating both charts, export them:

```bash
cd /Users/viraatchaudhary/projects/tesla-telemetry-lakehouse/infra
./export-dashboards.sh
```

This creates `superset/dashboards_export.zip` which will be:
- Automatically imported on Superset startup
- Included in the project for recruiters

---

## ✅ Verification

1. Refresh Superset dashboard
2. You should see:
   - ✅ 2 charts displaying data
   - ✅ Auto-refresh enabled (10 min)
   - ✅ Both charts updating with new data

---

## 🎯 What Recruiters Will See

When they run `docker-compose up -d`:
1. ✅ MinIO bucket auto-created
2. ✅ Superset auto-initialized
3. ✅ Admin user created (admin/admin)
4. ✅ PostgreSQL driver installed
5. ✅ Dashboards auto-imported
6. ✅ Charts showing live data (after 15 min)

---

## 📝 Notes

- First chart creation might take a moment
- If no data appears, wait 10 more minutes for batch job to run
- Charts will be empty initially, then populate as data flows
- Auto-refresh ensures charts stay current

**Ready to create the dashboards? Follow the steps above!** 🚀
