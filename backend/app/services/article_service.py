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

HOW SESSIONS FLOW THROUGH YOUR APP:
------------------------------------
  FastAPI request
      │
      ▼
  Depends(get_db)  →  creates session, yields it
      │
      ▼
  Route handler  →  calls article_service.save_articles(db, data)
      │
      ▼
  Service function  →  uses db to query/insert, returns result
      │
      ▼
  Route handler  →  returns response to client
      │
      ▼
  Finally block  →  session.close() returns connection to pool

WHY NO db.commit() INSIDE THE SERVICE?
---------------------------------------
The route handler owns the session lifecycle. It decides when to commit.
This keeps the service "pure" — it only does database operations, not
transaction management. The route pattern looks like:

    @router.post("/ingest")
    def ingest_articles(db: Session = Depends(get_db)):
        articles = news_service.fetch_articles("AI")
        saved = article_service.save_articles(db, articles)
        db.commit()          # ← route decides when to commit
        return {"saved": len(saved)}

If anything fails before commit, the session is rolled back automatically
when it closes. No partial data ever gets saved.
"""
from app.ml.ranking import calculate_article_score
from typing import Any, Sequence
from app.ml.personalization import personalize_score
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article


# ── Save ──────────────────────────────────────────────────────────────

def save_articles(
    db: Session,
    articles_data: list[dict[str, Any]],
) -> list[Article]:
    """
    Save a batch of articles, skipping any whose URL already exists.

    This is the main ingestion entry point. You pass it a list of
    normalized article dicts (from news_service._normalize) and it:

      1. Collects all URLs from the batch
      2. Queries the DB to find which URLs already exist
      3. Filters out duplicates (by URL)
      4. Inserts only new articles
      5. Returns the newly created Article objects

    WHY BULK DEDUPLICATE?
    ─────────────────────
    Naive approach: loop through articles, check one-by-one if URL exists.
    That's N+1 queries — terrible performance for 100 articles.

    This approach: 1 query to find all existing URLs, then filter in Python.
    Two database operations total (1 SELECT + 1 INSERT), regardless of batch size.

    Args:
        db:           SQLAlchemy session (from Depends(get_db))
        articles_data: List of article dicts with keys matching Article fields

    Returns:
        List of newly created Article objects (duplicates skipped)
    """
    if not articles_data:
        return []

    # ── Step 1: Collect all URLs from the incoming batch ───────────────
    incoming_urls = [a["url"] for a in articles_data if a.get("url")]

    # ── Step 2: Find which URLs already exist in the database ──────────
    # This is ONE query, no matter how many URLs we're checking.
    existing_urls: set[str] = set()
    if incoming_urls:
        stmt = select(Article.url).where(Article.url.in_(incoming_urls))
        result = db.execute(stmt)
        existing_urls = {row[0] for row in result}

    # ── Step 3: Filter out duplicates and create Article objects ────────
    new_articles: list[Article] = []
    seen_urls: set[str] = set()  # catch duplicates within the same batch

    for data in articles_data:
        url = data.get("url")
        if not url or url in existing_urls or url in seen_urls:
            continue

        seen_urls.add(url)

        # Only pass fields the Article model actually has.
        # Extra keys in the dict (like "language" from NewsAPI when null)
        # are safely ignored — they just become NULL columns.
        article = Article(
            title=data.get("title"),
            description=data.get("description"),
            content=data.get("content"),
            source=data.get("source"),
            url=url,
            image_url=data.get("image_url"),
            author=data.get("author"),
            published_at=data.get("published_at"),
            category=data.get("category"),
            language=data.get("language"),
            popularity_score=data.get("popularity_score"),
            sentiment_score=data.get("sentiment_score"),
        )
        new_articles.append(article)

    # ── Step 4: Bulk insert all new articles at once ───────────────────
    # add_all + flush sends a single INSERT … RETURNING to PostgreSQL.
    # The objects get their id, created_at, updated_at populated by the DB.
    if new_articles:
        db.add_all(new_articles)
        db.flush()  # sends SQL to DB but does NOT commit

    return new_articles


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
):
    """
    Fetch articles and rank them using personalization logic.
    """

    articles = get_articles(db, limit=limit)

    ranked_articles = []

    for article in articles:
        base_score = calculate_article_score(article)

        score = personalize_score(
            article,
            base_score,
        )

        ranked_articles.append(
            {
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "category": article.category,
                "source": article.source,
                "url": article.url,
                "image_url": article.image_url,
                "published_at": article.published_at,
                "score": score,
            }
        )

    ranked_articles.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return ranked_articles

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
