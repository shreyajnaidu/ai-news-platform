import unittest
from unittest.mock import MagicMock, patch

from app.services.article_service import CleanupResult
from app.services.ingestion_service import run_ingestion


class IngestionServiceTests(unittest.TestCase):
    @patch("app.services.ingestion_service.acquire_ingestion_lock", return_value=False)
    def test_skips_when_another_job_holds_lock(self, _lock: MagicMock) -> None:
        result = run_ingestion(
            MagicMock(),
            queries=["technology"],
            page_size=20,
            retention_days=30,
            max_rows=10_000,
        )

        self.assertEqual(result.status, "skipped_locked")
        self.assertEqual(result.fetched, 0)

    @patch("app.services.ingestion_service.clean_articles")
    @patch("app.services.ingestion_service.save_articles")
    @patch("app.services.ingestion_service.fetch_articles")
    @patch("app.services.ingestion_service.acquire_ingestion_lock", return_value=True)
    def test_reports_pipeline_metrics(
        self,
        _lock: MagicMock,
        fetch: MagicMock,
        save: MagicMock,
        clean: MagicMock,
    ) -> None:
        fetch.side_effect = [
            [{"url": "one"}, {"url": "two"}],
            [{"url": "two"}],
        ]
        save.return_value = [MagicMock(), MagicMock()]
        clean.return_value = CleanupResult(4, 3, 90)

        result = run_ingestion(
            MagicMock(),
            queries=["technology", " AI "],
            page_size=20,
            retention_days=30,
            max_rows=10_000,
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.queries, ["technology", "AI"])
        self.assertEqual(result.fetched, 3)
        self.assertEqual(result.inserted, 2)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.deleted_old, 4)
        self.assertEqual(result.deleted_over_cap, 3)
        self.assertEqual(result.remaining, 90)


if __name__ == "__main__":
    unittest.main()
