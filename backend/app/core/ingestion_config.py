"""Configuration used only by the standalone news ingestion worker."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    newsapi_key: str | None = None
    ingestion_queries: str = "technology,artificial intelligence"
    news_page_size: int = 20
    article_retention_days: int = 30
    article_max_rows: int = 10_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


ingestion_settings = IngestionSettings()
