from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


USER_INTERESTS = [
    "artificial intelligence",
    "machine learning",
    "technology",
    "startups",
    "software engineering",
    "world news",
]


def rank_articles_by_interest(articles: list[dict]) -> list[dict]:
    """
    ML-powered ranking using TF-IDF + cosine similarity.
    """

    if not articles:
        return articles

    documents = []

    for article in articles:
        text = " ".join(
            [
                article.get("title", ""),
                article.get("description", ""),
                article.get("category", ""),
            ]
        )

        documents.append(text)

    user_profile = " ".join(USER_INTERESTS)

    all_text = [user_profile] + documents

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=500,
    )

    tfidf_matrix = vectorizer.fit_transform(all_text)

    user_vector = tfidf_matrix[0:1]
    article_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(
        user_vector,
        article_vectors,
    )[0]

    for article, score in zip(articles, similarities):
        article["ml_score"] = float(score)

    ranked = sorted(
        articles,
        key=lambda x: x["ml_score"],
        reverse=True,
    )

    return ranked