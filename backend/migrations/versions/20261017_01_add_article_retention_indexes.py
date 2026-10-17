"""Baseline the existing schema and add ingestion indexes.

Revision ID: 20261017_01
Revises:
Create Date: 2026-10-17
"""

from alembic import op


revision = "20261017_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing deployments already have these tables from create_all(). Using
    # IF NOT EXISTS also makes this root migration usable for fresh databases.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(150),
            is_active BOOLEAN DEFAULT true NOT NULL,
            interests TEXT,
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            title VARCHAR(500) NOT NULL,
            description TEXT,
            content TEXT,
            source VARCHAR(200),
            url VARCHAR(2048) NOT NULL UNIQUE,
            image_url VARCHAR(2048),
            author VARCHAR(200),
            published_at TIMESTAMP WITHOUT TIME ZONE,
            category VARCHAR(100),
            language VARCHAR(5),
            popularity_score NUMERIC,
            sentiment_score NUMERIC,
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_active_created "
        "ON users (is_active, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_articles_category "
        "ON articles (category)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_articles_category_published "
        "ON articles (category, published_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_articles_popularity_published "
        "ON articles (popularity_score, published_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_articles_created_at "
        "ON articles (created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_articles_published_at "
        "ON articles (published_at)"
    )


def downgrade() -> None:
    # This baseline adopts pre-existing production objects, so downgrade must
    # not remove tables or indexes that may predate Alembic.
    pass
