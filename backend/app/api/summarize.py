"""
app/api/summarize.py
====================
Route handler for AI-powered article summarization.

ENDPOINT:
---------
  POST /articles/summarize

  The frontend sends:
    { "title": "...", "content": "...", "source": "..." }

RESPONSE CONTRACT:
------------------
  The frontend expects this EXACT JSON shape:
  {
    "summary": ["bullet one", "bullet two", "bullet three"],
    "sentiment": "positive",
    "reading_time": "3 min read"
  }

  DO NOT change the key names or types without updating the frontend's
  SummaryResult interface in summarizer.ts.

ERROR HANDLING:
---------------
  422  → Missing or empty content
  502  → AI service failure (network, auth, rate limit)
  504  → AI service timeout
  500  → Unexpected server error (parsed AI response, etc.)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.summarizer_service import (
    summarize_text,
    SummarizerError,
    GeminiAPIError,
    GeminiResponseError,
)


# ── Request Schema ──────────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    """Payload the frontend sends to request a summary."""
    title: str = Field(default="", description="Article headline")
    content: str = Field(..., min_length=1, description="Article body text")
    source: str = Field(default="", description="Publisher name")


# ── Router ──────────────────────────────────────────────────────────────

router = APIRouter()


# ── Endpoint ────────────────────────────────────────────────────────────

@router.post("/summarize")
async def get_article_summary(request: SummarizeRequest):
    """
    Generate an AI summary for article text.

    Flow:
      1. Receive title, content, source from the frontend
      2. Call summarize_text() → OpenRouter API
      3. Parse structured response (bullets + sentiment)
      4. Return JSON matching the frontend contract

    Args:
        request: SummarizeRequest with title, content, source.

    Returns:
        JSON with summary, sentiment, and reading_time.
    """
    try:
        result = await summarize_text(
            title=request.title,
            content=request.content,
            source=request.source,
        )
        return result.to_dict()

    except SummarizerError as exc:
        error_message = str(exc)

        # No content to summarize
        if "no content" in error_message.lower():
            raise HTTPException(
                status_code=422,
                detail=error_message,
            )

        # AI service errors (auth, rate limit, network, server)
        if isinstance(exc, GeminiAPIError):
            status_code = exc.status_code

            # Rate limit
            if status_code == 429:
                raise HTTPException(
                    status_code=502,
                    detail="AI service is busy — please try again in a moment",
                )

            # Auth failure
            if status_code in (401, 403):
                raise HTTPException(
                    status_code=502,
                    detail="AI service authentication failed",
                )

            # Timeout
            if "timed out" in error_message.lower():
                raise HTTPException(
                    status_code=504,
                    detail="AI service took too long to respond",
                )

            # Other API errors
            raise HTTPException(
                status_code=502,
                detail="AI service temporarily unavailable",
            )

        # AI response parsing errors
        if isinstance(exc, GeminiResponseError):
            raise HTTPException(
                status_code=500,
                detail="Failed to parse AI response — please try again",
            )

        # Generic fallback
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the summary",
        )
