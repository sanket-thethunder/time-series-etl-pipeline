#!/usr/bin/env python3
"""
main.py
-------
Entry point for the ETL pipeline.

Run once:
    python main.py

Run with scheduler (set scheduler.enabled=true in config.yaml):
    python main.py
"""

import logging
import logging.config
import os
import sys

import yaml

from etl.pipeline import ETLPipeline



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def setup_logging(log_cfg: dict) -> None:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_cfg.get("level", "INFO")),
        format=log_cfg.get("format", "%(asctime)s [%(levelname)s] %(name)s - %(message)s"),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_cfg.get("file", "logs/etl.log")),
        ],
    )


def run_pipeline(config: dict) -> None:
    pipeline = ETLPipeline(config)
    result = pipeline.run()
    if result["success"]:
        print(f"✅  Pipeline succeeded — {result['rows_inserted']} new rows inserted.")
    else:
        print(f"❌  Pipeline failed: {result['error']}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    config = load_config()
    setup_logging(config.get("logging", {}))

    scheduler_cfg = config.get("scheduler", {})

    if scheduler_cfg.get("enabled", False):
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
        except ImportError:
            print("APScheduler not installed. Run:  pip install apscheduler")
            sys.exit(1)

        interval_hours = scheduler_cfg.get("interval_hours", 6)
        scheduler = BlockingScheduler()
        scheduler.add_job(run_pipeline, "interval", hours=interval_hours, args=[config])
        print(f"🕐  Scheduler started — running every {interval_hours} hour(s). Ctrl-C to stop.")

        # Run once immediately on start
        run_pipeline(config)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("Scheduler stopped.")
    else:
        run_pipeline(config)


if __name__ == "__main__":
    main()
