from app.ml.preprocessing import prepare_article_text


CATEGORY_KEYWORDS = {
    "Technology": [
        "ai",
        "technology",
        "software",
        "startup",
        "apple",
        "google",
        "microsoft",
        "tesla",
        "robot",
        "chip",
    ],
    "Finance": [
        "stock",
        "market",
        "finance",
        "economy",
        "crypto",
        "bitcoin",
        "investment",
        "bank",
    ],
    "Sports": [
        "football",
        "cricket",
        "nba",
        "soccer",
        "tennis",
        "fifa",
        "match",
    ],
    "Politics": [
        "election",
        "government",
        "minister",
        "president",
        "policy",
        "parliament",
    ],
}


def classify_article(title: str, description: str | None) -> str:
    """
    Simple keyword-based article classification.
    """

    text = prepare_article_text(title, description)

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword in text:
                score += 1

        scores[category] = score

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "General"

    return best_category