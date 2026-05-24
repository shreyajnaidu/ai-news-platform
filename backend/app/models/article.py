"""
app/models/article.py
=====================
The Article model — the core table for your AI news recommendation platform.

Every news item your system ingests becomes a row here. The fields are
designed to support the full pipeline:

  1. Ingestion   → title, url, source, author, published_at, content
  2. NLP         → category, sentiment_score, language
  3. Ranking     → popularity_score
  4. Recommend   → all fields combined feed your ML scoring logic

Inherits from BaseModel which already provides: id, created_at, updated_at.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class Article(BaseModel):
    __tablename__ = "articles"

    # ── Core news fields ───────────────────────────────────────────────
    # These come straight from the news source (API, RSS, scraper).

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Article headline",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Short summary / snippet from the source",
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full article body text (populated after scraping)",
    )

    source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Publisher name: Reuters, TechCrunch, etc.",
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        unique=True,
        comment="Canonical URL — unique to prevent duplicate ingestion",
    )

    image_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="Thumbnail / hero image",
    )

    author: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Original author byline",
    )

    published_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="When the article was published (from the source, not our DB)",
    )

    # ── NLP / Classification fields ────────────────────────────────────
    # Populated by your ML pipeline after ingestion.

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="NLP-assigned category: Technology, Health, Politics, etc.",
    )

    language: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        comment="ISO 639-1 code: en, hi, fr, de, etc.",
    )

    # ── Scoring fields ─────────────────────────────────────────────────
    # Used by the ranking and recommendation engine.

    popularity_score: Mapped[Decimal | None] = mapped_column(
        nullable=True,
        comment="Aggregated popularity 0.00–100.00 (clicks, shares, recency)",
    )

    sentiment_score: Mapped[Decimal | None] = mapped_column(
        nullable=True,
        comment="Sentiment -1.00 (negative) to +1.00 (positive)",
    )

    # ── Indexes ────────────────────────────────────────────────────────
    # Speed up the queries your app will actually run.

    __table_args__ = (
        # Most common query: "latest articles in category X"
        Index("ix_articles_category_published", "category", "published_at"),
        # Recommendation query: "top articles by popularity, recent first"
        Index("ix_articles_popularity_published", "popularity_score", "published_at"),
    )

    # ── Representation ─────────────────────────────────────────────────
    # Makes logging and debugging readable.
    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title!r}>"