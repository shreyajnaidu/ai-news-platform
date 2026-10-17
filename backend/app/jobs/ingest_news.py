"""Command-line entry point for the scheduled news ingestion job."""

import argparse
from dataclasses import asdict
import json
import logging
import sys

from app.core.ingestion_config import ingestion_settings
from app.db.database import SessionLocal
from app.services.ingestion_service import run_ingestion


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and retain current news")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="NewsAPI query; may be supplied multiple times",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=ingestion_settings.news_page_size,
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=ingestion_settings.article_retention_days,
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=ingestion_settings.article_max_rows,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queries = args.queries or ingestion_settings.ingestion_queries.split(",")
    db = SessionLocal()

    try:
        result = run_ingestion(
            db,
            queries=queries,
            page_size=args.page_size,
            retention_days=args.retention_days,
            max_rows=args.max_rows,
        )
        db.commit()
        logger.info("ingestion_metrics=%s", json.dumps(asdict(result)))
        return 0
    except Exception:
        db.rollback()
        logger.exception("News ingestion failed")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
