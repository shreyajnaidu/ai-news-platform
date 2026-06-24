from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_optional_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.article_service import (
    get_ranked_articles,
    save_articles,
)
from app.services.news_service import (
    NewsAPIError,
    fetch_articles,
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
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    try:
        user_interests = None
        if current_user and current_user.interests:
            try:
                parsed = json.loads(current_user.interests)
                if isinstance(parsed, list):
                    user_interests = parsed
            except (json.JSONDecodeError, TypeError):
                pass

        ranked_articles = get_ranked_articles(
            db,
            user_interests=user_interests,
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