"""tests/test_extract.py — Unit tests for WeatherExtractor."""

import pytest
import responses  # pip install responses
import requests

from etl.extract import WeatherExtractor

BASE_URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 19.076,
    "longitude": 72.877,
    "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"],
    "timezone": "Asia/Kolkata",
    "forecast_days": 7,
}

MOCK_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
        "temperature_2m": [28.5, 27.1],
        "relative_humidity_2m": [75, 78],
        "wind_speed_10m": [12.3, 10.1],
        "precipitation": [0.0, 0.2],
    }
}


@responses.activate
def test_extract_success():
    responses.add(responses.GET, BASE_URL, json=MOCK_RESPONSE, status=200)
    extractor = WeatherExtractor(BASE_URL, PARAMS)
    data = extractor.extract()
    assert "hourly" in data
    assert len(data["hourly"]["time"]) == 2


@responses.activate
def test_extract_http_error():
    responses.add(responses.GET, BASE_URL, status=500)
    extractor = WeatherExtractor(BASE_URL, PARAMS)
    with pytest.raises(requests.HTTPError):
        extractor.extract()


def test_flatten_params_list():
    extractor = WeatherExtractor(BASE_URL, PARAMS)
    assert isinstance(extractor.params["hourly"], str)
    assert "temperature_2m" in extractor.params["hourly"]
