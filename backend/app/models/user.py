"""
app/models/user.py
==================
User model for authentication and personalized recommendations.

DESIGN DECISIONS:
-----------------
  - email is the login identifier (not username) — industry standard
  - hashed_password stores bcrypt output — NEVER plain text
  - is_active allows admin-level soft-deletes without data loss
  - interests stores a JSON list for personalized recommendation tracking
  - Uniqueness enforced at DB level (unique constraint + index)

FUTURE EXTENSIBILITY:
---------------------
  The interests JSON field is designed for the recommendation engine.
  When a user reads articles, their interest profile grows:

    ["artificial intelligence", "geopolitics", "startups"]

  The recommendation_service can then weight articles differently
  per-user instead of using global defaults.

  For more advanced personalization (click tracking, read history,
  explicit likes/dislikes), add a separate UserInteraction table
  later. This model stays focused on identity + basic preferences.

INHERITS:
  BaseModel → id, created_at, updated_at
"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class User(BaseModel):
    """
    User account for authentication and personalization.

    Columns:
        email            — unique login identifier
        hashed_password  — bcrypt hash (never stored as plain text)
        full_name        — display name (optional at signup)
        is_active        — soft-delete flag; inactive users can't log in
        interests        — JSON list of topic strings for recommendation tuning
    """

    __tablename__ = "users"

    # ── Identity ───────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Login email — unique across all users",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash via passlib — never store plain text",
    )

    full_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        comment="Display name — optional at signup",
    )

    # ── Account state ──────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Soft-delete: inactive users can't authenticate",
    )

    # ── Personalization ────────────────────────────────────────────────
    # Stores a JSON array of interest strings.
    # Example: ["artificial intelligence", "geopolitics", "startups"]
    # Used by recommendation_service for per-user ranking weights.
    interests: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='JSON array of interest topics, e.g. ["AI", "startups"]',
    )

    # ── Indexes ────────────────────────────────────────────────────────
    # email already indexed via unique=True above.
    # Composite index for admin queries like "show active users sorted by newest".
    __table_args__ = (
        Index("ix_users_active_created", "is_active", "created_at"),
    )

    # ── Representation ─────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
