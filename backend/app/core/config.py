"""
app/core/config.py
==================
Central configuration for the entire application.

WHY THIS FILE EXISTS:
---------------------
Instead of scattering os.environ.get() calls everywhere, we read ALL
configuration once at startup into a single Settings object. This gives us:

  1. Type safety        - DATABASE_URL is guaranteed to be a string
  2. Validation         - pydantic will error immediately if required vars are missing
  3. Testability        - tests can override settings easily
  4. Single source of truth - one place to see every config knob

HOW IT WORKS:
-------------
- pydantic-settings reads from environment variables automatically.
- It also reads from a .env file (if present) so you don't have to
  export vars every time you open a new terminal.
- The Settings() instance is created once and imported wherever needed.

BEGINNER NOTE:
--------------
Think of this file as the "control panel" for your app. Every external
value your app needs (database URL, port, debug mode, etc.) lives here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.

    Each attribute below corresponds to an environment variable with the same name.
    For example, `database_url` looks for the DATABASE_URL env var.

    If you add a new config value, just add an attribute here with a type
    and a default (if optional). That's it.
    """

    # ── Database ──────────────────────────────────────────────────────
    # Neon PostgreSQL connection string.
    # Example: postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
    database_url: str

    # ── OpenRouter AI ────────────────────────────────────────────────
    # OpenRouter API key for article summarization (OpenAI-compatible).
    # Get one at: https://openrouter.ai/keys
    openrouter_api_key: str

    # ── JWT Authentication ──────────────────────────────────────────
    # SECRET_KEY signs JWT tokens — must be a long random string.
    # Generate one: python -c "import secrets; print(secrets.token_urlsafe(32))"
    # NEVER commit a real secret to git. Always use .env.
    secret_key: str

    # How long a login token remains valid (in minutes).
    # 60 min = good balance of security and UX.
    # Shorter (15-30 min) for high-security apps.
    access_token_expire_minutes: int = 60

    # JWT signing algorithm. HS256 (HMAC-SHA256) is the standard
    # for symmetric-key tokens and is supported by every JWT library.
    jwt_algorithm: str = "HS256"

    # ── App ───────────────────────────────────────────────────────────
    app_name: str = "AI News Ranker"
    debug: bool = False

    # ── Pydantic-settings config ──────────────────────────────────────
    # This tells pydantic-settings to:
    #   1. Look for a .env file in the project root
    #   2. Ignore extra env vars (don't crash if something unexpected exists)
    #   3. Make env var names case-insensitive
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# ── Singleton instance ────────────────────────────────────────────────
# This is created ONCE when the module is first imported.
# Every other file that does `from app.core.config import settings`
# gets the SAME object. No duplication, no wasted parsing.
settings = Settings()
