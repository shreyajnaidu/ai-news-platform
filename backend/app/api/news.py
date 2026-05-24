from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.article_service import (
    get_ranked_articles,
    save_articles,
)
from app.services.news_service import (
    NewsAPIError,
    fetch_articles,
)
from app.services.recommendation_service import (
    rank_articles_by_interest,
)
router = APIRouter()


@router.get("/news")
def get_news(
    query: str = "technology",
    db: Session = Depends(get_db),
):
    try:
        articles = fetch_articles(query=query)

        saved_articles = save_articles(db, articles)

        db.commit()

        return {
            "message": "Articles fetched and stored successfully",
            "saved_count": len(saved_articles),
            "articles": articles,
        }

    except NewsAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/feed")
def get_feed(
    db: Session = Depends(get_db),
):
    try:
        ranked_articles = get_ranked_articles(db)

        ranked_articles = rank_articles_by_interest(
           ranked_articles
        )

        return {
            "count": len(ranked_articles),
            "feed": ranked_articles,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
    )