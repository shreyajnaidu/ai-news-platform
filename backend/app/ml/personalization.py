from app.models.article import Article


USER_INTERESTS = {
    "Technology": 1.5,
    "Finance": 1.3,
    "Politics": 1.0,
    "Sports": 0.8,
    "General": 0.7,
}


def personalize_score(
    article: Article,
    base_score: float,
) -> float:
    """
    Boost article score based on user interests.
    """

    interest_weight = USER_INTERESTS.get(
        article.category,
        1.0,
    )

    personalized_score = base_score * interest_weight

    return round(personalized_score, 2)