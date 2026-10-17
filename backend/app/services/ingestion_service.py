"""Orchestrates one locked news ingestion and retention transaction."""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.article_service import clean_articles, save_articles
from app.services.news_service import fetch_articles


INGESTION_LOCK_ID = 1_847_293_611


@dataclass(frozen=True)
class IngestionResult:
    status: str
    queries: list[str]
    fetched: int
    inserted: int
    skipped: int
    deleted_old: int
    deleted_over_cap: int
    remaining: int


def acquire_ingestion_lock(db: Session) -> bool:
    """Prevent concurrent jobs; the transaction-scoped lock releases on commit."""
    bind = db.get_bind()
    if bind.dialect.name != "postgresql":
        return True

    return bool(
        db.scalar(
            text("SELECT pg_try_advisory_xact_lock(:lock_id)"),
            {"lock_id": INGESTION_LOCK_ID},
        )
    )


def run_ingestion(
    db: Session,
    *,
    queries: list[str],
    page_size: int,
    retention_days: int,
    max_rows: int,
) -> IngestionResult:
    """Fetch, insert, and clean articles without committing the transaction."""
    normalized_queries = [query.strip() for query in queries if query.strip()]
    if not normalized_queries:
        raise ValueError("at least one ingestion query is required")
    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")

    if not acquire_ingestion_lock(db):
        return IngestionResult(
            status="skipped_locked",
            queries=normalized_queries,
            fetched=0,
            inserted=0,
            skipped=0,
            deleted_old=0,
            deleted_over_cap=0,
            remaining=0,
        )

    articles = []
    for query in normalized_queries:
        articles.extend(fetch_articles(query=query, page_size=page_size))

    saved_articles = save_articles(db, articles)
    cleanup = clean_articles(
        db,
        retention_days=retention_days,
        max_rows=max_rows,
    )

    return IngestionResult(
        status="success",
        queries=normalized_queries,
        fetched=len(articles),
        inserted=len(saved_articles),
        skipped=len(articles) - len(saved_articles),
        deleted_old=cleanup.deleted_old,
        deleted_over_cap=cleanup.deleted_over_cap,
        remaining=cleanup.remaining,
    )
