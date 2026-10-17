"""
app/services/article_service.py
================================
Database operations for the Article model — save, deduplicate, fetch.

DESIGN PHILOSOPHY:
------------------
Every function takes a `db: Session` as its first argument. This is
called "dependency injection" and it means:

  1. The service never creates or closes sessions — the caller does
  2. The same session is reused within a single request (transaction)
  3. Tests can pass in a fake session without touching real PostgreSQL

INGESTION FLOW:
---------------
The standalone ingestion job owns the session and transaction. This service
uses PostgreSQL ON CONFLICT for atomic URL deduplication, then applies the age
retention and hard row cap before the job commits everything together.

WHY NO db.commit() INSIDE THE SERVICE?
---------------------------------------
The caller owns the session lifecycle. It decides when to commit.
This keeps the service "pure" — it only does database operations, not
transaction management. The worker pattern looks like:

    db = SessionLocal()
    saved = article_service.save_articles(db, articles)
    db.commit()

If anything fails before commit, the worker rolls back the transaction. No
partial data gets saved.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.article import Article
from app.services.recommendation_service import rank_articles


@dataclass(frozen=True)
class CleanupResult:
    deleted_old: int
    deleted_over_cap: int
    remaining: int


# ── Save ──────────────────────────────────────────────────────────────

def save_articles(
    db: Session,
    articles_data: list[dict[str, Any]],
) -> list[Article]:
    """
    Bulk-insert valid articles and atomically skip URLs already in PostgreSQL.

    Duplicates within the incoming batch are removed in Python. Database-level
    ON CONFLICT handles existing URLs and concurrent insert attempts safely.

    Args:
        db:           SQLAlchemy session (from Depends(get_db))
        articles_data: List of article dicts with keys matching Article fields

    Returns:
        List of newly created Article objects (duplicates skipped)
    """
    if not articles_data:
        return []

    rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for data in articles_data:
        url = data.get("url")
        title = data.get("title")
        if not url or not title or url in seen_urls:
            continue

        seen_urls.add(url)
        rows.append(
            {
                "title": title,
                "description": data.get("description"),
                "content": data.get("content"),
                "source": data.get("source"),
                "url": url,
                "image_url": data.get("image_url"),
                "author": data.get("author"),
                "published_at": data.get("published_at"),
                "category": data.get("category"),
                "language": data.get("language"),
                "popularity_score": data.get("popularity_score"),
                "sentiment_score": data.get("sentiment_score"),
            }
        )

    if not rows:
        return []

    stmt = (
        insert(Article)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[Article.url])
        .returning(Article)
    )
    return list(db.scalars(stmt).all())


def clean_articles(
    db: Session,
    retention_days: int,
    max_rows: int,
    *,
    now: datetime | None = None,
) -> CleanupResult:
    """Delete expired articles, then enforce an absolute table-size cap."""
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")
    if max_rows < 1:
        raise ValueError("max_rows must be at least 1")

    cutoff = (now or datetime.utcnow()) - timedelta(days=retention_days)
    old_result = db.execute(
        delete(Article).where(Article.created_at < cutoff)
    )

    # Keep the newest rows. id is a deterministic tie-breaker for equal timestamps.
    excess_ids = (
        select(Article.id)
        .order_by(Article.created_at.desc(), Article.id.desc())
        .offset(max_rows)
    )
    cap_result = db.execute(
        delete(Article).where(Article.id.in_(excess_ids))
    )
    remaining = db.scalar(select(func.count()).select_from(Article)) or 0

    return CleanupResult(
        deleted_old=old_result.rowcount or 0,
        deleted_over_cap=cap_result.rowcount or 0,
        remaining=remaining,
    )


# ── Fetch ─────────────────────────────────────────────────────────────

def get_articles(
    db: Session,
    limit: int = 50,
) -> Sequence[Article]:
    """
    Fetch the most recent articles from the database.

    Ordered by published_at descending (newest first). This is the query
    your main feed will use: "show me the latest news."

    Args:
        db:    SQLAlchemy session
        limit: Max articles to return (default 50)

    Returns:
        Sequence of Article objects
    """
    stmt = (
        select(Article)
        .order_by(Article.published_at.desc().nulls_last())
        .limit(limit)
    )
    result = db.execute(stmt)
    return result.scalars().all()


def get_articles_by_category(
    db: Session,
    category: str,
    limit: int = 50,
) -> Sequence[Article]:
    """
    Fetch recent articles filtered by NLP-assigned category.

    Uses the composite index ix_articles_category_published for speed.
    This is the query behind "show me Technology news" or "Health news."

    Args:
        db:       SQLAlchemy session
        category: NLP category to filter by (case-sensitive exact match)
        limit:    Max articles to return

    Returns:
        Sequence of Article objects in that category
    """
    stmt = (
        select(Article)
        .where(Article.category == category)
        .order_by(Article.published_at.desc().nulls_last())
        .limit(limit)
    )
    result = db.execute(stmt)
    return result.scalars().all()

def get_ranked_articles(
    db: Session,
    limit: int = 20,
    user_interests: list[str] | None = None,
):
    """
    Fetch articles and rank them using the unified recommendation engine.

    Uses recommendation_service.rank_articles which computes:
      - ML-based interest scores
      - Editorial importance boosts
      - Freshness time-decay
      - Quality penalties
      - Per-user personalization (if user_interests provided)

    Args:
        db:              SQLAlchemy session.
        limit:           Max articles to fetch before ranking.
        user_interests:  Optional list of interest topics for personalization.

    Returns:
        List of article dicts with score keys (ml_score, importance_boost,
        freshness_boost, quality_score, final_score), sorted by final_score.
    """

    articles = get_articles(db, limit=limit)

    article_dicts = []
    for article in articles:
        article_dicts.append(
            {
                "id": article.id,
                "title": article.title or "",
                "description": article.description or "",
                "content": article.content or "",
                "category": article.category or "",
                "source": article.source or "",
                "url": article.url,
                "image_url": article.image_url,
                "published_at": article.published_at,
            }
        )

    ranked = rank_articles(article_dicts, user_interests=user_interests)

    return ranked

def get_article_by_url(
    db: Session,
    url: str,
) -> Article | None:
    """
    Look up a single article by its URL.

    Useful for checking if an article exists before processing it,
    or for fetching full article details by canonical URL.

    Args:
        db:  SQLAlchemy session
        url: The article's canonical URL

    Returns:
        Article object if found, None otherwise
    """
    stmt = select(Article).where(Article.url == url)
    result = db.execute(stmt)
    return result.scalars().first()
