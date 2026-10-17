import unittest
from unittest.mock import patch

import requests

from app.services.news_service import NewsAPIError, fetch_articles


class NewsServiceTests(unittest.TestCase):
    @patch("app.services.news_service.requests.get")
    @patch("app.services.news_service.ingestion_settings.newsapi_key", "secret-key")
    def test_network_errors_do_not_expose_api_key(self, get) -> None:
        get.side_effect = requests.RequestException(
            "failed https://newsapi.org/v2/everything?apiKey=secret-key"
        )

        with self.assertRaisesRegex(
            NewsAPIError,
            "^Network error calling NewsAPI$",
        ) as raised:
            fetch_articles("technology")

        self.assertNotIn("secret-key", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
