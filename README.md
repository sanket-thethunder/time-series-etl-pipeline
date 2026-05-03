# 🌦️ ETL Data Pipeline — Weather Forecast

A production-style Python ETL pipeline that extracts hourly weather forecast data
from the [Open-Meteo](https://open-meteo.com/) public API, transforms it into a
clean tabular format, and loads it into a SQLite (or PostgreSQL) database.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ETL Pipeline                               │
│                                                                     │
│  ┌──────────────┐     ┌──────────────────┐     ┌────────────────┐  │
│  │   EXTRACT    │     │    TRANSFORM     │     │     LOAD       │  │
│  │              │     │                  │     │                │  │
│  │ Open-Meteo   │────▶│ • Rename cols    │────▶│ SQLite /      │  │
│  │ REST API     │     │ • Cast types     │     │ PostgreSQL     │  │
│  │              │     │ • Drop nulls     │     │                │  │
│  │ WeatherEx-   │     │ • Dedup rows     │     │ DatabaseLoader │  │
│  │ tractor      │     │ • Add metadata   │     │ (upsert safe)  │  │
│  └──────────────┘     │                  │     └────────────────┘  │
│                        │ WeatherTransfor- │                        │
│                        │ mer              │                        │
│                        └──────────────────┘                        │
│                                                                    │
│  Orchestrated by: ETLPipeline  ◀──  main.py  ◀──  APScheduler     │
└─────────────────────────────────────────────────────────────────────

Config ──> config/config.yaml
Logs   ──> logs/etl.log
DB     ──> data/weather.db
```

---

## Project Structure

```
etl_pipeline/
├── config/
│   └── config.yaml          # All runtime settings (API params, DB, logging)
├── data/                    # SQLite database lives here (git-ignored)
├── etl/
│   ├── __init__.py
│   ├── extract.py           # WeatherExtractor — pulls raw API data
│   ├── transform.py         # WeatherTransformer — cleans & reshapes data
│   ├── load.py              # DatabaseLoader — upserts into DB
│   └── pipeline.py          # ETLPipeline — orchestrates E → T → L
├── logs/                    # Rotating log files (git-ignored)
├── tests/
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_load.py
├── main.py                  # Entry point
├── pyproject.toml           # pytest config
├── requirements.txt
└── .gitignore
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/sanket-thethunder/time-series-etl-pipeline.git
cd time-series-etl-pipeline
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

Edit `config/config.yaml` to set your target city coordinates and preferred database.

```yaml
api:
  params:
    latitude: 19.0760    # Change to your city
    longitude: 72.8777
```

### 3. Run the Pipeline

```bash
python main.py
```

Example output:
```
2024-01-01 12:00:00 [INFO] etl.extract - Extracting weather data...
2024-01-01 12:00:01 [INFO] etl.extract - Extraction successful — 168 hourly records available
2024-01-01 12:00:01 [INFO] etl.transform - Transformation complete — 168 rows
2024-01-01 12:00:01 [INFO] etl.load - Load complete — 168 new rows inserted (total: 168)
  Pipeline succeeded — 168 new rows inserted.
```

### 4. Enable Scheduler (Optional)

Set `scheduler.enabled: true` in `config.yaml` to run automatically every N hours
using APScheduler.

---

## Running Tests

```bash
pytest
```

All tests use an in-memory SQLite database and mocked HTTP responses — no internet
connection or external DB required.

---

## Database Schema

| Column            | Type      | Description                      |
|-------------------|-----------|----------------------------------|
| `id`              | INTEGER   | Auto-increment primary key       |
| `timestamp`       | TIMESTAMP | Forecast hour (local time)       |
| `temperature_c`   | REAL      | Temperature in °C                |
| `humidity_pct`    | INTEGER   | Relative humidity (%)            |
| `wind_speed_kmh`  | REAL      | Wind speed at 10 m (km/h)        |
| `precipitation_mm`| REAL      | Precipitation (mm)               |
| `latitude`        | REAL      | Location latitude                |
| `longitude`       | REAL      | Location longitude               |
| `fetched_at`      | TIMESTAMP | UTC timestamp of the pipeline run|

Unique constraint on `(timestamp, latitude, longitude)` ensures idempotent loads.

---

## Switching to PostgreSQL

1. Install the adapter: `pip install psycopg2-binary`
2. Update `config.yaml`:
   ```yaml
   database:
     type: "postgresql"
     postgresql_url: "postgresql://user:password@localhost:5432/etl_db"
   ```
3. Update the `CREATE TABLE` SQL in `load.py` — replace `AUTOINCREMENT` with
   `SERIAL` and `INSERT OR IGNORE` with `INSERT ... ON CONFLICT DO NOTHING`.

---

## Tech Stack

| Tool            | Role                          |
|-----------------|-------------------------------|
| `requests`      | HTTP client for API calls     |
| `pandas`        | Data transformation           |
| `SQLAlchemy`    | DB abstraction / ORM          |
| `PyYAML`        | Config file parsing           |
| `APScheduler`   | Optional cron-style scheduler |
| `pytest`        | Unit testing                  |
| `responses`     | Mock HTTP in tests            |
