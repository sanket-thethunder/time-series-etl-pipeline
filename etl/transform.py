"""
etl/transform.py
----------------
Cleans and reshapes the raw API payload into a tidy DataFrame
ready for loading into the database.
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class WeatherTransformer:
    """Transforms raw Open-Meteo JSON into a normalised pandas DataFrame."""

    REQUIRED_HOURLY_FIELDS = {
        "time",
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "precipitation",
    }

    def __init__(self, location_lat: float, location_lon: float):
        self.location_lat = location_lat
        self.location_lon = location_lon

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def transform(self, raw: dict[str, Any]) -> pd.DataFrame:
        """
        Convert the raw API payload to a clean DataFrame.

        Args:
            raw: Parsed JSON returned by WeatherExtractor.

        Returns:
            pd.DataFrame with columns:
                timestamp, temperature_c, humidity_pct,
                wind_speed_kmh, precipitation_mm,
                latitude, longitude, fetched_at
        """
        logger.info("Starting transformation")
        hourly = raw.get("hourly", {})
        self._validate(hourly)

        df = pd.DataFrame(hourly)

        df = self._rename_columns(df)
        df = self._cast_types(df)
        df = self._add_metadata(df)
        df = self._drop_nulls(df)
        df = self._remove_duplicates(df)

        logger.info("Transformation complete — %d rows", len(df))
        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate(self, hourly: dict) -> None:
        missing = self.REQUIRED_HOURLY_FIELDS - set(hourly.keys())
        if missing:
            raise ValueError(f"Missing fields in API response: {missing}")

    @staticmethod
    def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "time": "timestamp",
                "temperature_2m": "temperature_c",
                "relative_humidity_2m": "humidity_pct",
                "wind_speed_10m": "wind_speed_kmh",
                "precipitation": "precipitation_mm",
            }
        )

    @staticmethod
    def _cast_types(df: pd.DataFrame) -> pd.DataFrame:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for col in ["temperature_c", "wind_speed_kmh", "precipitation_mm"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["humidity_pct"] = pd.to_numeric(df["humidity_pct"], errors="coerce").astype(
            "Int64"
        )
        return df

    def _add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        df["latitude"] = self.location_lat
        df["longitude"] = self.location_lon
        df["fetched_at"] = pd.Timestamp.utcnow()
        return df

    @staticmethod
    def _drop_nulls(df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.dropna(subset=["timestamp", "temperature_c"])
        dropped = before - len(df)
        if dropped:
            logger.warning("Dropped %d rows with null critical values", dropped)
        return df

    @staticmethod
    def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates(subset=["timestamp", "latitude", "longitude"])
        dropped = before - len(df)
        if dropped:
            logger.warning("Removed %d duplicate rows", dropped)
        return df
