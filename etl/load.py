"""
etl/load.py
-----------
Handles database connection and upsert logic via SQLAlchemy.
Supports SQLite (default) and PostgreSQL.
"""

import logging

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# SQL to create the target table (SQLite / PostgreSQL compatible)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weather_hourly (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TIMESTAMP   NOT NULL,
    temperature_c   REAL,
    humidity_pct    INTEGER,
    wind_speed_kmh  REAL,
    precipitation_mm REAL,
    latitude        REAL        NOT NULL,
    longitude       REAL        NOT NULL,
    fetched_at      TIMESTAMP   NOT NULL,
    UNIQUE (timestamp, latitude, longitude)
);
"""


class DatabaseLoader:
    """Loads a transformed DataFrame into the database."""

    def __init__(self, db_config: dict):
        self.engine = self._build_engine(db_config)
        self._ensure_table()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load(self, df: pd.DataFrame) -> int:
        """
        Upsert *df* into weather_hourly.

        Rows that already exist (same timestamp + location) are skipped
        via INSERT OR IGNORE (SQLite) so re-running the pipeline is safe.

        Args:
            df: Clean DataFrame from WeatherTransformer.

        Returns:
            Number of new rows inserted.
        """
        if df.empty:
            logger.warning("DataFrame is empty — nothing to load")
            return 0

        before = self._row_count()
        # Write to a staging table first, then merge
        df.to_sql("_weather_staging", self.engine, if_exists="replace", index=False)

        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT OR IGNORE INTO weather_hourly
                        (timestamp, temperature_c, humidity_pct,
                         wind_speed_kmh, precipitation_mm,
                         latitude, longitude, fetched_at)
                    SELECT
                        timestamp, temperature_c, humidity_pct,
                        wind_speed_kmh, precipitation_mm,
                        latitude, longitude, fetched_at
                    FROM _weather_staging
                    """
                )
            )
            conn.execute(text("DROP TABLE IF EXISTS _weather_staging"))

        after = self._row_count()
        inserted = after - before
        logger.info("Load complete — %d new rows inserted (total: %d)", inserted, after)
        return inserted

    def close(self) -> None:
        self.engine.dispose()
        logger.debug("Database connection closed")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_engine(db_config: dict) -> Engine:
        db_type = db_config.get("type", "sqlite")
        if db_type == "sqlite":
            path = db_config.get("sqlite_path", "data/weather.db")
            url = f"sqlite:///{path}"
        elif db_type == "postgresql":
            url = db_config["postgresql_url"]
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        logger.info("Connecting to %s database", db_type)
        return create_engine(url, echo=False)

    def _ensure_table(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(CREATE_TABLE_SQL))
        logger.debug("Ensured weather_hourly table exists")

    def _row_count(self) -> int:
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM weather_hourly"))
            return result.scalar()
