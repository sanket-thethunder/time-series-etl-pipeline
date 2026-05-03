"""
etl/pipeline.py
---------------
Orchestrates Extract → Transform → Load in one place.
"""

import logging
from typing import Any

from etl.extract import WeatherExtractor
from etl.transform import WeatherTransformer
from etl.load import DatabaseLoader

logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    High-level orchestrator that wires together the three ETL stages.

    Usage:
        pipeline = ETLPipeline(config)
        result = pipeline.run()
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        api_cfg = config["api"]
        db_cfg = config["database"]

        self.extractor = WeatherExtractor(
            base_url=api_cfg["base_url"],
            params=api_cfg["params"],
        )
        self.transformer = WeatherTransformer(
            location_lat=api_cfg["params"]["latitude"],
            location_lon=api_cfg["params"]["longitude"],
        )
        self.loader = DatabaseLoader(db_config=db_cfg)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """
        Execute the full ETL pipeline.

        Returns:
            A summary dict with keys: success, rows_inserted, error.
        """
        summary: dict[str, Any] = {"success": False, "rows_inserted": 0, "error": None}

        try:
            logger.info("=== ETL Pipeline starting ===")

            # 1. Extract
            raw_data = self.extractor.extract()

            # 2. Transform
            df = self.transformer.transform(raw_data)

            # 3. Load
            rows = self.loader.load(df)

            summary["success"] = True
            summary["rows_inserted"] = rows
            logger.info("=== ETL Pipeline finished — %d rows inserted ===", rows)

        except Exception as exc:
            summary["error"] = str(exc)
            logger.exception("Pipeline failed: %s", exc)

        finally:
            self.loader.close()

        return summary
