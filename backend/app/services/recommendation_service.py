"""
app/services/recommendation_service.py
=======================================
Hybrid article ranking system — ML model + heuristic boosts.

ARCHITECTURE
------------
  rank_articles(articles)
      |
      ├─► _compute_ml_scores(articles)          ← trained model predict_proba()
      |
      ├─► _compute_importance_boost(articles)   ← category / keyword boosting
      |
      ├─► _compute_freshness_boost(articles)    ← time-decay from published_at
      |
      ├─► _compute_quality_penalty(articles)    ← penalize gossip / clickbait
      |
      └─► _merge_scores(...)                    ← weighted blend → final sort

WHY HYBRID, NOT ML-ONLY?
--------------------------
  A pure ML model captures *topical relevance* (does this article match
  the user's interests?) but misses editorial signals:

    - An AI article from 2 weeks ago is less valuable than one from 2 hours ago
    - A geopolitical scoop matters more than a celebrity tweet
    - Clickbait inflates engagement without adding value

  The hybrid approach lets the ML model do what it's good at (classify
  topics) while heuristics handle what the model can't see (time, source
  quality, editorial importance).

SCORING FORMULA
---------------
  final_score = (
      W_ML        * ml_score           +   # trained model output [0, 1]
      W_IMPORTANCE* importance_boost    +   # category / keyword lift
      W_FRESHNESS * freshness_boost     +   # time-decay curve
      W_QUALITY   * quality_score       # 1.0 (clean) → 0.3 (gossip)
  )

  All sub-scores are normalised to [0, 1] before blending.
  Weights sum to 1.0 so the final score also stays in [0, 1].

MODEL FILES
-----------
  - news_model.pkl      → trained LogisticRegression (predict_proba)
  - vectorizer.pkl      → trained TfidfVectorizer (transform input)

  Both are loaded once at module import via joblib. If the files don't
  exist, the service degrades gracefully — ml_score defaults to 0.5
  (neutral) and the heuristic boosters carry the ranking.

INPUT CONTRACT
--------------
  articles: list[dict]  — each dict must have:
      - title: str
      - description: str   (optional, defaults to "")
      - content: str       (optional, defaults to "")
      - category: str      (optional, defaults to "general")
      - source: str        (optional, defaults to "")
      - published_at: str  (ISO 8601 or None)

OUTPUT CONTRACT
---------------
  The same list[dict], with these keys ADDED (never removed):
      - ml_score:           float  [0, 1]
      - importance_boost:   float  [0, 1]
      - freshness_boost:    float  [0, 1]
      - quality_score:      float  [0.3, 1.0]
      - final_score:        float  [0, 1]

  Sorted by final_score descending.
"""

import logging
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

logger = logging.getLogger(__name__)


# ─── Model Loading ────────────────────────────────────────────────────────
# Load once at module import. If files are missing, log a warning and
# degrade gracefully — ml_score will always be 0.5 (neutral).

_MODEL_DIR = Path(__file__).resolve().parents[1] / "ml"

_model = None
_vectorizer = None

try:
    _model_path = _MODEL_DIR / "news_model.pkl"
    _vec_path = _MODEL_DIR / "vectorizer.pkl"

    if _model_path.exists() and _vec_path.exists():
        _model = joblib.load(_model_path)
        _vectorizer = joblib.load(_vec_path)
        logger.info("ML model and vectorizer loaded from %s", _MODEL_DIR)
    else:
        logger.warning(
            "ML model files not found at %s — ranking will use heuristics only. "
            "Expected: news_model.pkl, vectorizer.pkl",
            _MODEL_DIR,
        )
except Exception as exc:
    logger.error("Failed to load ML model: %s", exc)
    _model = None
    _vectorizer = None


# ─── Scoring Weights ──────────────────────────────────────────────────────
# These control how much each signal contributes to the final score.
# They sum to 1.0 so the blended score stays in [0, 1].
#
# TUNING GUIDE:
#   - Want smarter topic matching?    Raise W_ML
#   - Want breaking news first?       Raise W_FRESHNESS
#   - Want editorial curation feel?   Raise W_IMPORTANCE
#   - Want cleaner feed?              Raise W_QUALITY

W_ML = 0.40
W_IMPORTANCE = 0.25
W_FRESHNESS = 0.20
W_QUALITY = 0.15

# ─── Freshness Configuration ──────────────────────────────────────────────
# Half-life in hours: an article loses half its freshness boost every
# FRESHNESS_HALF_LIFE hours. 12h means today's news is king, yesterday's
# is half as fresh, and last week's is nearly zero.
FRESHNESS_HALF_LIFE_HOURS = 12.0

# Articles older than this get zero freshness boost (epoch fallback)
FRESHNESS_MAX_AGE_HOURS = 168  # 7 days

# ─── Importance Boosting ──────────────────────────────────────────────────
# Categories that are editorially important get a boost. This is not
# about personalization — it's about editorial judgment: these topics
# matter more for an informed professional audience.
#
# Format: lowercase category → boost multiplier [0, 1]
#   1.0 = maximum boost, 0.0 = no boost

IMPORTANCE_CATEGORY_BOOST: dict[str, float] = {
    "artificial intelligence": 1.0,
    "ai": 1.0,
    "geopolitics": 0.95,
    "geopolitical": 0.95,
    "economy": 0.90,
    "economics": 0.90,
    "technology": 0.85,
    "tech": 0.85,
    "startups": 0.80,
    "startup": 0.80,
    "breaking news": 0.90,
    "breaking": 0.90,
    "cybersecurity": 0.75,
    "climate": 0.70,
    "science": 0.70,
    "policy": 0.65,
    "defense": 0.65,
    "finance": 0.65,
    "national security": 0.65,
}

# Keywords that signal high importance — checked against title + description.
# These catch important articles that might have a generic category.

IMPORTANCE_KEYWORDS: list[str] = [
    "breaking",
    "exclusive",
    "investigation",
    "crisis",
    "summit",
    "treaty",
    "sanctions",
    "regulation",
    "legislation",
    "landmark",
    "historic",
    "cyberattack",
    "data breach",
    "ai breakthrough",
    "openai",
    "deepmind",
    "nuclear",
    "war",
    "conflict",
    "ceasefire",
    "ipo",
    "acquisition",
    "merger",
    "layoff",
    "federal reserve",
    "interest rate",
    "inflation",
    "recession",
]

KEYWORD_BOOST_VALUE = 0.15  # added per keyword match (capped at 1.0)

# ─── Quality Penalty ──────────────────────────────────────────────────────
# Keywords and categories that signal low-quality / gossip content.
# Articles matching these get their quality_score reduced.

LOW_QUALITY_CATEGORIES: set[str] = {
    "entertainment",
    "celebrity",
    "gossip",
    "lifestyle",
    "fashion",
    "reality tv",
    "tabloid",
    "clickbait",
    "viral",
    "trending now",
    "buzz",
}

LOW_QUALITY_KEYWORDS: list[str] = [
    "celebrity",
    "gossip",
    "rumor",
    "rumoured",
    "scandal",
    "dating",
    "breakup",
    "divorce",
    "wardrobe malfunction",
    "fashion faux pas",
    "went viral",
    "broke the internet",
    "you won't believe",
    "shocking video",
    "must see",
    "click here",
    "leaked photo",
    " Kardashian",
    " Jenner",
    " influencer drama",
    " TikTok star",
    " reality star",
]

QUALITY_PENALTY_PER_HIT = 0.15   # subtracted per keyword match
MIN_QUALITY_SCORE = 0.3          # floor — even trash articles aren't zeroed


# ─── 1. ML Score ──────────────────────────────────────────────────────────


def _compute_ml_scores(articles: list[dict[str, Any]]) -> list[float]:
    """
    Predict user interest scores using the trained LogisticRegression model.

    HOW IT WORKS:
        1. Concatenate title + description + category into a single text field
           (this mirrors the training data format)
        2. Transform text using the pre-trained TF-IDF vectorizer
        3. Call predict_proba() — returns [P(not_interesting), P(interesting)]
        4. Take the positive-class probability as ml_score

    GRACEFUL DEGRADATION:
        If the model or vectorizer failed to load, every article gets 0.5
        (neutral). The other boosters still work, so the ranking degrades
        to "heuristic-only" — still useful, just less smart.

    Args:
        articles: List of article dicts.

    Returns:
        List of ml_scores in [0, 1], one per article.
    """
    if _model is None or _vectorizer is None:
        return [0.5] * len(articles)

    if not articles:
        return []

    # Build text corpus matching training format
    texts = []
    for article in articles:
        parts = [
            article.get("title", ""),
            article.get("description", ""),
            article.get("category", ""),
        ]
        texts.append(" ".join(p for p in parts if p))

    try:
        tfidf_matrix = _vectorizer.transform(texts)
        probas = _model.predict_proba(tfidf_matrix)

        # predict_proba returns shape (n_samples, n_classes)
        # We want the probability of the positive class (last column)
        # For binary classification: probas[:, 1]
        # For multi-class: take the max probability as "interest confidence"
        if probas.shape[1] == 2:
            scores = probas[:, 1].tolist()
        else:
            scores = probas.max(axis=1).tolist()

        return scores

    except Exception as exc:
        logger.error("ML scoring failed, falling back to neutral: %s", exc)
        return [0.5] * len(articles)


# ─── 2. Importance Boost ─────────────────────────────────────────────────


def _compute_importance_boost(articles: list[dict[str, Any]]) -> list[float]:
    """
    Boost articles in editorially important categories / with important keywords.

    WHY KEYWORD BOOSTING IN ADDITION TO CATEGORY?
        Many articles have category="general" even when they cover critical
        topics. Keywords catch these — a "breaking" article about sanctions
        should rank high regardless of its category tag.

    SCORING LOGIC:
        base_boost = IMPORTANCE_CATEGORY_BOOST.get(category, 0.0)
        keyword_boost = count of importance keyword matches * KEYWORD_BOOST_VALUE
        total = min(1.0, base_boost + keyword_boost)

    Args:
        articles: List of article dicts.

    Returns:
        List of importance_boost values in [0, 1], one per article.
    """
    boosts: list[float] = []

    for article in articles:
        # ── Category-based boost ──────────────────────────────────────
        category = (article.get("category") or "").strip().lower()
        base_boost = IMPORTANCE_CATEGORY_BOOST.get(category, 0.0)

        # ── Keyword-based boost ───────────────────────────────────────
        # Check title and description for importance signals
        text_to_search = " ".join([
            (article.get("title") or "").lower(),
            (article.get("description") or "").lower(),
        ])

        keyword_hits = 0
        for keyword in IMPORTANCE_KEYWORDS:
            if keyword.lower() in text_to_search:
                keyword_hits += 1

        keyword_boost = min(
            keyword_hits * KEYWORD_BOOST_VALUE,
            1.0 - base_boost,  # don't exceed 1.0 total
        )

        boosts.append(min(1.0, base_boost + keyword_boost))

    return boosts


# ─── 3. Freshness Boost ──────────────────────────────────────────────────


def _parse_published_at(raw: str | None) -> datetime | None:
    """
    Parse an ISO 8601 / NewsAPI-style datetime string into a timezone-aware datetime.

    Handles these common formats:
        - "2025-01-15T14:30:00Z"           (ISO 8601 UTC)
        - "2025-01-15T14:30:00+00:00"      (ISO 8601 with offset)
        - "2025-01-15T14:30:00.000Z"       (with milliseconds)
        - "2025-01-15 14:30:00"            (naive, assumed UTC)

    Returns None if parsing fails — the article gets zero freshness.
    """
    if not raw:
        return None
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
    return raw

    raw = str(raw).strip()

    # Try ISO 8601 with 'Z' suffix
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    # Try standard fromisoformat (Python 3.11+ handles most cases)
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass

    # Fallback: try common news API format
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _compute_freshness_boost(articles: list[dict[str, Any]]) -> list[float]:
    """
    Score articles based on how recently they were published.

    DECAY CURVE:
        We use exponential decay with a configurable half-life:

            freshness = 2 ** (-age_hours / HALF_LIFE)

        This means:
        - Age 0h   → freshness = 1.0   (just published)
        - Age 12h  → freshness = 0.5   (half-life)
        - Age 24h  → freshness = 0.25
        - Age 48h  → freshness = 0.0625
        - Age 168h → freshness ≈ 0.003  (effectively zero)

    WHY EXPONENTIAL, NOT LINEAR?
        Linear decay (freshness = 1 - age/max) creates a uniform slope.
        Exponential decay creates a steep initial drop-off then a long tail.
        This matches real news consumption: the difference between 1h and 2h
        old matters a lot; the difference between 100h and 101h doesn't.

    MISSING published_at:
        Articles without a timestamp get a small default boost (0.2) so they
        aren't completely buried — they might be undated but still valuable.

    Args:
        articles: List of article dicts.

    Returns:
        List of freshness_boost values in [0, 1], one per article.
    """
    now = datetime.now(timezone.utc)
    boosts: list[float] = []

    for article in articles:
        published = _parse_published_at(article.get("published_at"))

        if published is None:
            boosts.append(0.2)  # small default for undated articles
            continue

        age_hours = max(0.0, (now - published).total_seconds() / 3600.0)

        if age_hours > FRESHNESS_MAX_AGE_HOURS:
            boosts.append(0.0)
            continue

        # Exponential decay: 2^(-age / half_life)
        freshness = 2.0 ** (-age_hours / FRESHNESS_HALF_LIFE_HOURS)
        boosts.append(max(0.0, min(1.0, freshness)))

    return boosts


# ─── 4. Quality Penalty ──────────────────────────────────────────────────


def _compute_quality_score(articles: list[dict[str, Any]]) -> list[float]:
    """
    Penalize low-quality, gossip, and clickbait articles.

    SCORING LOGIC:
        Start at 1.0 (perfect quality). Subtract QUALITY_PENALTY_PER_HIT
        for each low-quality signal detected (category match or keyword hit).
        Floor at MIN_QUALITY_SCORE so articles are never fully zeroed —
        they're just deprioritized, not censored.

    WHY NOT REMOVE THEM ENTIRELY?
        Censorship is not the job of a ranking system. A user might
        genuinely want to see entertainment news. The penalty ensures
        gossip doesn't dominate the feed, but it doesn't erase it.

    DETECTION SIGNALS:
        1. Category match — article.category in LOW_QUALITY_CATEGORIES
        2. Keyword match  — title or description contains LOW_QUALITY_KEYWORDS

    Args:
        articles: List of article dicts.

    Returns:
        List of quality_score values in [MIN_QUALITY_SCORE, 1.0], one per article.
    """
    scores: list[float] = []

    for article in articles:
        score = 1.0

        # ── Category penalty ──────────────────────────────────────────
        category = (article.get("category") or "").strip().lower()
        if category in LOW_QUALITY_CATEGORIES:
            score -= QUALITY_PENALTY_PER_HIT

        # ── Keyword penalty ───────────────────────────────────────────
        text_to_search = " ".join([
            (article.get("title") or "").lower(),
            (article.get("description") or "").lower(),
        ])

        keyword_hits = 0
        for keyword in LOW_QUALITY_KEYWORDS:
            if keyword.lower() in text_to_search:
                keyword_hits += 1

        score -= keyword_hits * QUALITY_PENALTY_PER_HIT

        # ── Floor at minimum ──────────────────────────────────────────
        scores.append(max(MIN_QUALITY_SCORE, score))

    return scores


# ─── 5. Score Merging ────────────────────────────────────────────────────


def _merge_scores(
    ml_scores: list[float],
    importance_boosts: list[float],
    freshness_boosts: list[float],
    quality_scores: list[float],
) -> list[float]:
    """
    Blend all sub-scores into a single final_score using configured weights.

    FORMULA:
        final = W_ML * ml + W_IMPORTANCE * importance
              + W_FRESHNESS * freshness + W_QUALITY * quality

    All weights sum to 1.0, so the result stays in [0, 1] as long as
    all inputs are in [0, 1] (which they are by construction).

    WHY WEIGHTED SUM, NOT MULTIPLICATIVE?
        Multiplicative scoring (final = ml * freshness * quality) is harsh:
        if any single signal is 0, the entire score is 0. A great AI article
        that's 3 days old would score 0 under multiplicative freshness but
        still scores well under weighted sum — freshness just reduces it,
        it doesn't kill it.

    Args:
        ml_scores:          Model-predicted interest scores.
        importance_boosts:  Editorial importance signals.
        freshness_boosts:   Time-decay recency signals.
        quality_scores:     Content quality penalties applied.

    Returns:
        List of final_score values in [0, 1].
    """
    final_scores: list[float] = []

    for ml, imp, fresh, qual in zip(
        ml_scores, importance_boosts, freshness_boosts, quality_scores
    ):
        score = (
            W_ML * ml
            + W_IMPORTANCE * imp
            + W_FRESHNESS * fresh
            + W_QUALITY * qual
        )
        # Clamp to [0, 1] for safety (floating-point edge cases)
        final_scores.append(max(0.0, min(1.0, score)))

    return final_scores


# ─── Public Entry Point ──────────────────────────────────────────────────


def rank_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Rank articles using the hybrid scoring system.

    This is the main public API. It takes a list of article dicts,
    computes all sub-scores, merges them, and returns the same list
    (with score keys added) sorted by final_score descending.

    PIPELINE:
        1. Compute ML scores            (trained model or neutral fallback)
        2. Compute importance boosts     (category + keyword signals)
        3. Compute freshness boosts      (exponential time-decay)
        4. Compute quality scores        (penalize gossip / clickbait)
        5. Merge all scores              (weighted sum)
        6. Attach scores to article dicts
        7. Sort by final_score descending

    SIDE EFFECTS:
        Adds these keys to each article dict IN-PLACE:
            - ml_score:           float
            - importance_boost:   float
            - freshness_boost:    float
            - quality_score:      float
            - final_score:        float

    Args:
        articles: List of article dicts. Each should have (at minimum):
            title, description (opt), category (opt),
            source (opt), published_at (opt).

    Returns:
        The same list[dict], with score keys added, sorted by final_score
        descending. Returns an empty list if input is empty.
    """
    if not articles:
        return []

    # ── Step 1–4: Compute all sub-scores ──────────────────────────────
    ml_scores = _compute_ml_scores(articles)
    importance_boosts = _compute_importance_boost(articles)
    freshness_boosts = _compute_freshness_boost(articles)
    quality_scores = _compute_quality_score(articles)

    # ── Step 5: Merge into final scores ───────────────────────────────
    final_scores = _merge_scores(
        ml_scores, importance_boosts, freshness_boosts, quality_scores
    )

    # ── Step 6: Attach scores to articles ─────────────────────────────
    for article, ml, imp, fresh, qual, final in zip(
        articles,
        ml_scores,
        importance_boosts,
        freshness_boosts,
        quality_scores,
        final_scores,
    ):
        article["ml_score"] = round(ml, 4)
        article["importance_boost"] = round(imp, 4)
        article["freshness_boost"] = round(fresh, 4)
        article["quality_score"] = round(qual, 4)
        article["final_score"] = round(final, 4)

    # ── Step 7: Sort by final_score descending ────────────────────────
    ranked = sorted(articles, key=lambda a: a["final_score"], reverse=True)

    return ranked

    # ─── Backward Compatibility ───────────────────────────────────────────

rank_articles_by_interest = rank_articles