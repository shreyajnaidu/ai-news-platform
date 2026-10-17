import unittest
from unittest.mock import MagicMock

from sqlalchemy.dialects import postgresql

from app.services.article_service import save_articles


class SaveArticlesTests(unittest.TestCase):
    def test_builds_one_atomic_upsert_for_valid_unique_urls(self) -> None:
        db = MagicMock()
        inserted = MagicMock()
        db.scalars.return_value.all.return_value = [inserted]

        result = save_articles(
            db,
            [
                {"title": "First", "url": "https://example.com/one"},
                {"title": "Duplicate", "url": "https://example.com/one"},
                {"title": "", "url": "https://example.com/no-title"},
                {"title": "No URL", "url": None},
            ],
        )

        statement = db.scalars.call_args.args[0]
        compiled = statement.compile(dialect=postgresql.dialect())
        sql = str(compiled)

        self.assertEqual(result, [inserted])
        self.assertIn("ON CONFLICT (url) DO NOTHING", sql)
        self.assertEqual(compiled.params["url_m0"], "https://example.com/one")
        self.assertNotIn("url_m1", compiled.params)


if __name__ == "__main__":
    unittest.main()
