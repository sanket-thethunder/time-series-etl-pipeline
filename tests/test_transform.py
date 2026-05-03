"""tests/test_transform.py — Unit tests for WeatherTransformer."""

import pytest
import pandas as pd

from etl.transform import WeatherTransformer

LAT, LON = 19.076, 72.877

VALID_RAW = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [28.5, 27.1, None],
        "relative_humidity_2m": [75, 78, 80],
        "wind_speed_10m": [12.3, 10.1, 9.5],
        "precipitation": [0.0, 0.2, 0.1],
    }
}


@pytest.fixture
def transformer():
    return WeatherTransformer(location_lat=LAT, location_lon=LON)


def test_transform_returns_dataframe(transformer):
    df = transformer.transform(VALID_RAW)
    assert isinstance(df, pd.DataFrame)


def test_column_names(transformer):
    df = transformer.transform(VALID_RAW)
    expected = {"timestamp", "temperature_c", "humidity_pct", "wind_speed_kmh",
                "precipitation_mm", "latitude", "longitude", "fetched_at"}
    assert expected.issubset(set(df.columns))


def test_null_rows_dropped(transformer):
    # Row with None temperature_c should be dropped
    df = transformer.transform(VALID_RAW)
    assert df["temperature_c"].isna().sum() == 0


def test_metadata_added(transformer):
    df = transformer.transform(VALID_RAW)
    assert (df["latitude"] == LAT).all()
    assert (df["longitude"] == LON).all()


def test_missing_fields_raises(transformer):
    bad_raw = {"hourly": {"time": [], "temperature_2m": []}}
    with pytest.raises(ValueError, match="Missing fields"):
        transformer.transform(bad_raw)


def test_duplicate_removal(transformer):
    # Duplicate timestamps should be removed
    raw_with_dupes = {
        "hourly": {
            "time": ["2024-01-01T00:00", "2024-01-01T00:00"],
            "temperature_2m": [28.5, 28.5],
            "relative_humidity_2m": [75, 75],
            "wind_speed_10m": [12.3, 12.3],
            "precipitation": [0.0, 0.0],
        }
    }
    df = transformer.transform(raw_with_dupes)
    assert len(df) == 1
