"""
app/services/news_service.py
============================
Fetches articles from the NewsAPI.org /v2/everything endpoint and returns
them as clean, normalized dictionaries ready for your ML pipeline.

WHY A SEPARATE SERVICE (NOT IN THE ROUTE)?
-------------------------------------------
  - Routes handle HTTP     → request in, response out
  - Services handle logic  → call APIs, transform data, compute things

Keeping them separate means:
  - You can test this service without spinning up FastAPI
  - You can call fetch_articles() from a cron job, a CLI script, or tests
  - Your route handler stays thin (3 lines: call service, return result)

DATA FLOW:
----------
  Route handler
      │
      ▼
  fetch_articles(query, page_size)
      │
      ├─► _build_url()          ← assembles the full API URL
      │
      ├─► requests.get()        ← calls NewsAPI
      │
      ├─► _handle_response()    ← checks for errors, returns raw JSON
      │
      └─► _normalize()          ← maps each raw article → clean dict
      │
      ▼
  List[dict]  ← back to the route handler

BEGINNER NOTE:
--------------
Every function here is plain synchronous Python — no async, no generators,
no decorators. Just functions that take inputs and return outputs.
"""

import os
from datetime import datetime
from typing import Any
from app.ml.classifier import classify_article
import requests
from dotenv import load_dotenv

load_dotenv()
# ── Configuration ─────────────────────────────────────────────────────
# Read from .env or shell environment.
# Never hardcode API keys — they belong in .env (which is gitignored).
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

if not NEWSAPI_KEY:
    raise RuntimeError(
        "NEWSAPI_KEY is not set. "
        "Add it to your .env file: NEWSAPI_KEY=your_key_here"
    )

NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"


# ── Custom exceptions ─────────────────────────────────────────────────
# Why custom exceptions? So the route handler can catch them specifically
# and return the right HTTP status code:
#
#   except NewsAPIError:
#       raise HTTPException(status_code=502, detail="Upstream news API failed")
#
# This keeps the service unaware of HTTP — it only knows about news errors.

class NewsAPIError(Exception):
    """Raised when the NewsAPI call fails (network, auth, rate limit, etc.)."""
    pass


# ── Public function ───────────────────────────────────────────────────

def fetch_articles(
    query: str,
    page_size: int = 20,
    language: str = "en",
    sort_by: str = "publishedAt",
) -> list[dict[str, Any]]:
    """
    Fetch articles from NewsAPI.org.

    Args:
        query:       Search keywords (e.g. "artificial intelligence")
        page_size:   How many articles to return (1–100, default 20)
        language:    ISO 639-1 language code (default "en")
        sort_by:     NewsAPI sort order — publishedAt, relevancy, popularity

    Returns:
        A list of normalized article dicts. Each dict has these keys:
            title, description, content, source, url, image_url,
            author, published_at, language

    Raises:
        NewsAPIError: If the API call fails for any reason.
    """
    url = _build_url(query, page_size, language, sort_by)

    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as exc:
        raise NewsAPIError(f"Network error calling NewsAPI: {exc}") from exc

    raw_data = _handle_response(response)
    raw_articles = raw_data.get("articles", [])

    return [_normalize(article) for article in raw_articles]


# ── Private helpers ───────────────────────────────────────────────────

def _build_url(
    query: str,
    page_size: int,
    language: str,
    sort_by: str,
) -> str:
    """
    Assemble the full NewsAPI URL with query parameters.

    The URL looks like:
        https://newsapi.org/v2/everything?q=AI&pageSize=20&language=en&sortBy=publishedAt&apiKey=xxx
    """
    params = (
        f"?q={query}"
        f"&pageSize={page_size}"
        f"&language={language}"
        f"&sortBy={sort_by}"
        f"&apiKey={NEWSAPI_KEY}"
    )
    return NEWSAPI_BASE_URL + params


def _handle_response(response: requests.Response) -> dict[str, Any]:
    """
    Check the HTTP response and extract JSON.

    Handles three failure modes:
      1. Non-200 status code     → raise with the status code
      2. NewsAPI-specific error  → "status" field is "error" with a message
      3. Invalid JSON            → raise with parse error
    """
    if response.status_code != 200:
        raise NewsAPIError(
            f"NewsAPI returned HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise NewsAPIError(f"NewsAPI returned invalid JSON: {exc}") from exc

    # NewsAPI returns {"status": "error", "message": "..."} on API-level errors
    if data.get("status") == "error":
        raise NewsAPIError(f"NewsAPI error: {data.get('message', 'Unknown error')}")

    return data


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a raw NewsAPI article dict into a clean, consistent dict
    that matches your Article model fields.

    WHY NORMALIZE?
    ──────────────
    NewsAPI returns fields like:
        - "source": {"id": null, "name": "TechCrunch"}  ← nested object
        - "urlToImage": "https://..."                     ← camelCase
        - "publishedAt": "2025-05-22T14:30:00Z"           ← ISO string
        - "content": "Article text... [+1234 chars]"      ← truncated with suffix
        - "author": "By John Doe"                         ← sometimes prefixed

    Your database expects:
        - "source": "TechCrunch"                          ← flat string
        - "image_url": "https://..."                      ← snake_case
        - "published_at": datetime object                 ← parsed
        - "content": clean text                           ← no [+1234 chars]
        - "author": "John Doe"                            ← cleaned

    This function bridges that gap. Every downstream consumer (DB, ML,
    recommendation engine) gets consistent data without worrying about
    the external API's quirks.
    """
    # Extract source name from nested {"id": null, "name": "TechCrunch"}
    source = raw.get("source", {}) or {}
    source_name = source.get("name")

    # Clean the author field — NewsAPI sometimes prepends "By " or similar
    author = raw.get("author")
    if author and author.lower().startswith("by "):
        author = author[3:].strip()

    # Parse ISO timestamp → datetime object (None if missing/empty)
    published_at = None
    raw_date = raw.get("publishedAt")
    if raw_date:
        try:
            published_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            published_at = None

    # Strip NewsAPI's "[+NNN chars]" truncation marker from content
    content = raw.get("content")
    if content:
        import re
        content = re.sub(r"\s*\[\+\d+\s*chars\]$", "", content).strip() or None

    return {
        "title": raw.get("title"),
        "description": raw.get("description"),
        "content": content,
        "source": source_name,
        "url": raw.get("url"),
        "image_url": raw.get("urlToImage"),
        "author": author,
        "published_at": published_at,
        "language": raw.get("language"),
"category": classify_article(
    raw.get("title", ""),
    raw.get("description"),
),  # not always returned by /everything
    }