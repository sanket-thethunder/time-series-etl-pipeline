"""tests/test_load.py — Unit tests for DatabaseLoader using in-memory SQLite."""

import pandas as pd
import pytest

from etl.load import DatabaseLoader

IN_MEMORY_CONFIG = {"type": "sqlite", "sqlite_path": ":memory:"}


@pytest.fixture
def loader():
    ldr = DatabaseLoader(IN_MEMORY_CONFIG)
    yield ldr
    ldr.close()


def _sample_df(n: int = 3) -> pd.DataFrame:
    import pandas as pd
    return pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="h"),
        "temperature_c": [28.5, 27.1, 26.8][:n],
        "humidity_pct": [75, 78, 80][:n],
        "wind_speed_kmh": [12.3, 10.1, 9.5][:n],
        "precipitation_mm": [0.0, 0.2, 0.1][:n],
        "latitude": [19.076] * n,
        "longitude": [72.877] * n,
        "fetched_at": [pd.Timestamp.utcnow()] * n,
    })


def test_load_inserts_rows(loader):
    df = _sample_df(3)
    inserted = loader.load(df)
    assert inserted == 3


def test_load_idempotent(loader):
    df = _sample_df(3)
    loader.load(df)
    inserted_again = loader.load(df)
    assert inserted_again == 0  # duplicates are ignored


def test_load_empty_df(loader):
    empty = _sample_df(0)
    result = loader.load(empty)
    assert result == 0
