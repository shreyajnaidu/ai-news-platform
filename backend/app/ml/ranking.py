import random
from datetime import datetime

from app.models.article import Article


CATEGORY_WEIGHTS = {
    "Technology": 1.2,
    "Finance": 1.1,
    "Politics": 1.0,
    "Sports": 0.9,
    "General": 0.8,
}


def calculate_article_score(article: Article) -> float:
    """
    Ranking algorithm using:
    - category importance
    - recency
    - simulated popularity
    """

    score = 0.0

    # Category weight
    category_weight = CATEGORY_WEIGHTS.get(
        article.category,
        0.5,
    )

    score += category_weight * 10

    # Recency
    if article.published_at:
        now = datetime.utcnow()

        time_difference = now - article.published_at

        hours_old = time_difference.total_seconds() / 3600

        recency_score = max(0, 24 - hours_old)

        score += recency_score

    # Simulated popularity variation
    popularity_boost = random.uniform(1, 15)

    score += popularity_boost

    return round(score, 2)