import re


def clean_text(text: str) -> str:
    """
    Basic NLP preprocessing for article text.
    """

    # lowercase
    text = text.lower()

    # remove URLs
    text = re.sub(r"http\S+", "", text)

    # remove punctuation/special chars
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    # remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def prepare_article_text(title: str, description: str | None) -> str:
    """
    Combine title + description into one clean NLP string.
    """

    combined = title

    if description:
        combined += " " + description

    return clean_text(combined)