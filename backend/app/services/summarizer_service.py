"""
app/services/summarizer_service.py
==================================
AI-powered article summarization using OpenRouter (OpenAI-compatible API).

ARCHITECTURE
------------
Pure text-in, summary-out. No database, no article IDs.

  Caller (route handler)
      |
      v
  summarize_text(title, content, source)      <- public entry point
      |
      v
  await _call_openrouter(title, source, text) <- async via openai SDK
      |
      v
  _parse_ai_response(raw_text)                <- pure function, no I/O
      |
      v
  SummaryResult                               <- back to caller

WHY summarize_text() INSTEAD OF summarize_article()?
-----------------------------------------------------
  - The service is a pure AI layer — it knows nothing about the database.
  - The caller (route handler) is responsible for fetching the article
    and passing its text fields to this function.
  - This makes the service testable without a database, reusable from
    cron jobs or CLI scripts, and decoupled from the ORM.

PROVIDER
--------
Uses OpenRouter's OpenAI-compatible endpoint with the openai Python SDK.
Current model: openai/gpt-4o-mini (fast, cheap, good at structured output).

  from openai import AsyncOpenAI
  client = AsyncOpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=settings.openrouter_api_key,
  )

PROMPT ENGINEERING PHILOSOPHY
------------------------------
  - Concise, scannable bullet points (never paragraphs)
  - Professional tone without robotic qualifiers
  - Forced JSON output via response_format
  - Sentiment as a single label, not a paragraph of analysis

IMPORT CONTRACT
---------------
  Route handler imports:
      summarize_text, SummarizerError,
      GeminiAPIError, GeminiResponseError

  NOTE: GeminiAPIError and GeminiResponseError are backward-compatible
  aliases for AIServiceError and AIResponseError respectively.

  Config import:
      from app.core.config import settings
"""

import json
import math
import re
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings


# ─── Custom Exceptions ──────────────────────────────────────────────────


class SummarizerError(Exception):
    """Base exception for all summarizer failures."""
    pass


class AIServiceError(SummarizerError):
    """
    Raised when the AI provider API call fails.
    Covers: network errors, auth failures, rate limits, server errors.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AIResponseError(SummarizerError):
    """Raised when the AI provider returns a response that cannot be parsed."""
    pass


# Backward-compatible aliases — the route handler imports these by name.
# DO NOT remove them or the route will break.
GeminiAPIError = AIServiceError
GeminiResponseError = AIResponseError


# ─── Structured Result ──────────────────────────────────────────────────


class SummaryResult:
    """
    Structured summary that matches the frontend contract EXACTLY.

    Frontend expects:
        {
            "summary": string[],
            "sentiment": string,
            "reading_time": string
        }
    """

    __slots__ = ("summary", "sentiment", "reading_time")

    def __init__(
        self, summary: list[str], sentiment: str, reading_time: str
    ) -> None:
        self.summary = summary
        self.sentiment = sentiment
        self.reading_time = reading_time

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "sentiment": self.sentiment,
            "reading_time": self.reading_time,
        }


# ─── Constants ──────────────────────────────────────────────────────────

# Average adult reading speed: ~238 words/minute (Brysbaert 2019)
WORDS_PER_MINUTE = 238

# OpenRouter model identifier
MODEL_NAME = "openrouter/free"

# Valid sentiment labels the parser normalises to
VALID_SENTIMENTS = frozenset({"positive", "negative", "neutral", "mixed"})

# Fallback mapping for common AI sentiment variations
SENTIMENT_ALIASES: dict[str, str] = {
    "pos": "positive",
    "neg": "negative",
    "neu": "neutral",
    "somewhat positive": "positive",
    "somewhat negative": "negative",
    "mostly positive": "positive",
    "mostly negative": "negative",
    "mixed feelings": "mixed",
}


# ─── OpenRouter Client ──────────────────────────────────────────────────
# Initialised once at module load.  Uses AsyncOpenAI so every call
# stays non-blocking without manual thread offloading.

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """
    Lazy-initialise the AsyncOpenAI client for OpenRouter.

    WHY LAZY?
        The client reads settings.openrouter_api_key at creation time.
        Lazy init ensures the .env file has been loaded by pydantic-settings
        before we try to read the key.
    """
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
    return _client


# ─── Prompt Templates ───────────────────────────────────────────────────
#
# SUMMARY_USER_TEMPLATE uses str.format().
#   - Single braces  {title}  are format placeholders
#   - Double braces  {{  and  }}  produce literal { and } in the output

SUMMARY_SYSTEM_PROMPT = (
    "You are an expert news analyst. You distill articles into sharp, "
    "scannable intelligence briefs.\n"
    "\n"
    "RULES:\n"
    "- Return ONLY valid JSON — no markdown, no backticks, no commentary\n"
    "- Each bullet must be a self-contained insight (not a fragment)\n"
    "- Write for a professional who scans, not reads\n"
    '- Never start bullets with "The article" or "This article"\n'
    "- Use active voice\n"
    "- Be specific, not vague\n"
    '- Sentiment must be exactly one of: "positive", "negative", '
    '"neutral", "mixed"'
)

SUMMARY_USER_TEMPLATE = (
    "Analyze this news article and return a JSON object.\n"
    "\n"
    "TITLE: {title}\n"
    "SOURCE: {source}\n"
    "\n"
    "CONTENT:\n"
    "{content}\n"
    "\n"
    "Return JSON with this exact structure:\n"
    "{{\n"
    '  "bullets": [\n'
    '    "First key insight",\n'
    '    "Second key insight",\n'
    '    "Third key insight"\n'
    "  ],\n"
    '  "sentiment": "positive|negative|neutral|mixed"\n'
    "}}\n"
    "\n"
    "Requirements:\n"
    "- 3 to 5 bullets, each one sentence\n"
    "- Sentiment reflects the article's overall tone\n"
    "- Be precise and intelligent — not generic"
    "- Return ONLY valid JSON."
)


# ─── Reading Time Estimation ────────────────────────────────────────────


def _estimate_reading_time(text: str) -> str:
    """
    Estimate how long the full article takes to read.

    Uses the industry-standard 238 WPM average.  Rounds up to the
    nearest minute with a floor of 1 (no "0 min read").

    Args:
        text: Full article text (title + content joined).

    Returns:
        Human-readable string like "3 min read".
    """
    word_count = len(text.split())
    if word_count == 0:
        return "1 min read"
    minutes = max(1, math.ceil(word_count / WORDS_PER_MINUTE))
    return f"{minutes} min read"


# ─── OpenRouter API Call ────────────────────────────────────────────────


async def _call_openrouter(title: str, source: str, content: str) -> str:
    """
    Send a structured prompt to OpenRouter via the OpenAI SDK and return raw text.

    Uses AsyncOpenAI so the call stays non-blocking.  The SDK handles
    retries, timeouts, and HTTP/2 connection pooling internally.

    Configuration rationale:
        - temperature 0.3           → low creativity, high consistency
        - max_tokens 1024           → enough for 5 bullets, not for essays
        - response_format JSON      → forces structured JSON output
        - model openai/gpt-4o-mini  → fast, cheap, good at summaries

    Args:
        title:   Article headline.
        source:  Publisher name (e.g. "Reuters").
        content: Article body text (description + content).

    Returns:
        Raw text content from the model's response.

    Raises:
        AIServiceError:  On any API-level failure (auth, rate limit, network).
        AIResponseError: If the response structure is unexpected or empty.
    """
    user_text = SUMMARY_USER_TEMPLATE.format(
        title=title,
        source=source or "Unknown",
        content=content,
    )

    client = _get_client()

    # ── Call the API ─────────────────────────────────────────────────
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0.3,
            max_tokens=1024,
            
        )
    except Exception as exc:
        print("OPENROUTER ERROR:", repr(exc))
        error_name = type(exc).__name__
        error_message = str(exc)

        # ── Auth failures (401 / 403) ───────────────────────────────
        if "401" in error_message or "403" in error_message:
            raise AIServiceError(
                "OpenRouter authentication failed — check OPENROUTER_API_KEY",
                status_code=401,
            ) from exc

        # ── Rate limit (429) ────────────────────────────────────────
        if "429" in error_message:
            raise AIServiceError(
                "OpenRouter rate limit exceeded — try again in a moment",
                status_code=429,
            ) from exc

        # ── Timeout ─────────────────────────────────────────────────
        if "timeout" in error_message.lower() or "timed out" in error_message.lower():
            raise AIServiceError(
                f"OpenRouter API timed out: {error_name}",
                status_code=None,
            ) from exc

        # ── Connection / network errors ─────────────────────────────
        if "connection" in error_message.lower():
            raise AIServiceError(
                f"Network error calling OpenRouter: {error_name}",
                status_code=None,
            ) from exc

        # ── Server errors (5xx) ─────────────────────────────────────
        if any(code in error_message for code in ("500", "502", "503")):
            raise AIServiceError(
                f"OpenRouter server error: {error_name}",
                status_code=502,
            ) from exc

        # ── Generic catch-all ───────────────────────────────────────
        raise AIServiceError(
            f"OpenRouter API error ({error_name}): {error_message[:200]}",
            status_code=None,
        ) from exc

    # ── Extract text from response ───────────────────────────────────
    if not response.choices:
        raise AIResponseError("OpenRouter returned no choices")

    message = response.choices[0].message
    if not message or not message.content:
        raise AIResponseError("OpenRouter response has no content")

    text = message.content.strip()
    if not text:
        raise AIResponseError("OpenRouter response text is empty")

    return text


# ─── Response Parser ────────────────────────────────────────────────────


def _parse_ai_response(raw_text: str) -> tuple[list[str], str]:
    """
    Parse the AI model's JSON response into (bullet_points, sentiment_label).

    PURE FUNCTION — no I/O, no side effects.  Provider-agnostic: works
    with any model that returns JSON matching the prompt structure.

    Robustness features:
      - Strips markdown backtick wrappers (```json ... ```)
      - Handles multiple possible key names (bullets, summary, key_points)
      - Normalises nested sentiment objects {"label": "positive", "score": 0.8}
      - Maps common sentiment variations to the 4 valid labels
      - Falls back to regex extraction if primary JSON parse fails

    Args:
        raw_text: The text content from the model's response.

    Returns:
        Tuple of (bullet_point_strings, sentiment_label).

    Raises:
        AIResponseError: If parsing fails completely.
    """
    # ── Strip markdown wrapping ──────────────────────────────────────
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # ── Primary JSON parse ───────────────────────────────────────────
    parsed: dict[str, Any] | None = None
    try:
        candidate = json.loads(cleaned)
        if isinstance(candidate, dict):
            parsed = candidate
    except json.JSONDecodeError:
        pass

    # ── Fallback: extract first JSON object via regex ────────────────
    if parsed is None:
        json_match = re.search(r"\{[^{}]*\}", cleaned, re.DOTALL)
        if json_match:
            try:
                candidate = json.loads(json_match.group())
                if isinstance(candidate, dict):
                    parsed = candidate
            except json.JSONDecodeError:
                pass

    if parsed is None:
        raise AIResponseError(
            f"AI response is not valid JSON: {raw_text[:200]}"
        )

    # ── Extract bullet points ────────────────────────────────────────
    bullets_raw: Any = (
        parsed.get("bullets")
        or parsed.get("summary")
        or parsed.get("key_points")
        or parsed.get("points")
        or []
    )

    # Normalise to list of strings
    if isinstance(bullets_raw, str):
        bullets_raw = [
            line.strip().lstrip("-\u2022*0-9.) ")
            for line in bullets_raw.split("\n")
            if line.strip()
        ]
    elif not isinstance(bullets_raw, list):
        bullets_raw = []

    bullets: list[str] = []
    for item in bullets_raw:
        if isinstance(item, str):
            cleaned_item = item.strip().lstrip("-\u2022*0-9.) ").strip()
            if cleaned_item:
                bullets.append(cleaned_item)

    if not bullets:
        raise AIResponseError(
            "AI response contained no parseable bullet points"
        )

    # ── Extract and normalise sentiment ──────────────────────────────
    sentiment_raw: Any = parsed.get("sentiment", "neutral")

    if isinstance(sentiment_raw, dict):
        sentiment = str(sentiment_raw.get("label", "neutral")).strip().lower()
    elif isinstance(sentiment_raw, str):
        sentiment = sentiment_raw.strip().lower()
    else:
        sentiment = "neutral"

    if sentiment not in VALID_SENTIMENTS:
        sentiment = SENTIMENT_ALIASES.get(sentiment, "neutral")

    return bullets, sentiment


# ─── Public Entry Point ─────────────────────────────────────────────────


async def summarize_text(
    title: str,
    content: str,
    source: str = "",
) -> SummaryResult:
    """
    Generate an AI summary for article text using OpenRouter.

    Pure text-in, summary-out. No database, no article IDs.
    The caller is responsible for fetching the article and passing
    its fields here.

    Pipeline:
      1. Validate that content is not empty
      2. Call OpenRouter API                  (async, via openai SDK)
      3. Parse the structured JSON response   (pure function)
      4. Estimate reading time                (pure function)
      5. Return a SummaryResult               (matches frontend contract)

    Args:
        title:   Article headline.
        content: Article body text (description + content fields).
        source:  Publisher name (e.g. "Reuters"). Optional.

    Returns:
        SummaryResult with .summary (list[str]), .sentiment (str),
        and .reading_time (str).

    Raises:
        SummarizerError:  Content is empty.
        AIServiceError:   Network / auth / rate-limit / server failure.
        AIResponseError:  Unparseable AI output.
    """
    # ── 1. Validate input ────────────────────────────────────────────
    if not content or not content.strip():
        raise SummarizerError("No content provided to summarize")

    safe_title = title.strip() if title else "Untitled"
    safe_source = source.strip() if source else "Unknown Source"

    # ── 2. Call OpenRouter API ───────────────────────────────────────
    raw_response = await _call_openrouter(safe_title, safe_source, content)

    # ── 3. Parse the structured response ─────────────────────────────
    bullets, sentiment = _parse_ai_response(raw_response)

    # ── 4. Estimate reading time ─────────────────────────────────────
    full_text = " ".join(part for part in [safe_title, content] if part)
    reading_time = _estimate_reading_time(full_text)

    # ── 5. Return structured result ──────────────────────────────────
    return SummaryResult(
        summary=bullets,
        sentiment=sentiment,
        reading_time=reading_time,
    )