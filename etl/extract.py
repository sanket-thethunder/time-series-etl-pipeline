"""
etl/extract.py
--------------
Responsible for pulling raw data from the Open-Meteo weather API.
"""

import logging
import requests
from typing import Any

logger = logging.getLogger(__name__)


class WeatherExtractor:
    """Fetches hourly weather forecast data from the Open-Meteo API."""

    def __init__(self, base_url: str, params: dict[str, Any]):
        self.base_url = base_url
        self.params = self._flatten_params(params)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def extract(self) -> dict[str, Any]:
        """
        Hit the API and return the raw JSON payload.

        Returns:
            dict: Parsed JSON response from the API.

        Raises:
            requests.HTTPError: On non-2xx responses.
            requests.ConnectionError: On network failures.
        """
        logger.info("Extracting weather data from %s", self.base_url)
        try:
            response = requests.get(self.base_url, params=self.params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(
                "Extraction successful — %d hourly records available",
                len(data.get("hourly", {}).get("time", [])),
            )
            return data
        except requests.HTTPError as exc:
            logger.error("HTTP error during extraction: %s", exc)
            raise
        except requests.ConnectionError as exc:
            logger.error("Connection error during extraction: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _flatten_params(params: dict[str, Any]) -> dict[str, Any]:
        """
        Open-Meteo expects list values as repeated query params.
        requests handles lists natively, so we just return as-is.
        """
        flat = dict(params)
        if isinstance(flat.get("hourly"), list):
            flat["hourly"] = ",".join(flat["hourly"])
        return flat
