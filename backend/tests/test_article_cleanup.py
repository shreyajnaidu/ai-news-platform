import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.article import Article
from app.services.article_service import clean_articles


class CleanArticlesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def add_article(self, number: int, created_at: datetime) -> None:
        self.db.add(
            Article(
                title=f"Article {number}",
                url=f"https://example.com/{number}",
                created_at=created_at,
                updated_at=created_at,
            )
        )

    def test_deletes_expired_articles(self) -> None:
        now = datetime(2026, 10, 17, 12, 0, 0)
        self.add_article(1, now - timedelta(days=31))
        self.add_article(2, now - timedelta(days=29))
        self.db.flush()

        result = clean_articles(self.db, 30, 10_000, now=now)

        self.assertEqual(result.deleted_old, 1)
        self.assertEqual(result.deleted_over_cap, 0)
        self.assertEqual(result.remaining, 1)

    def test_keeps_only_newest_rows_at_cap(self) -> None:
        now = datetime(2026, 10, 17, 12, 0, 0)
        for number in range(5):
            self.add_article(number, now - timedelta(minutes=number))
        self.db.flush()

        result = clean_articles(self.db, 30, 3, now=now)
        remaining_urls = {
            article.url for article in self.db.query(Article).all()
        }

        self.assertEqual(result.deleted_old, 0)
        self.assertEqual(result.deleted_over_cap, 2)
        self.assertEqual(result.remaining, 3)
        self.assertEqual(
            remaining_urls,
            {
                "https://example.com/0",
                "https://example.com/1",
                "https://example.com/2",
            },
        )


if __name__ == "__main__":
    unittest.main()
