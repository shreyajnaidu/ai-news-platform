from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.security import get_optional_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.article_service import (
    get_articles,
    get_ranked_articles,
)

router = APIRouter()


@router.get("/news")
def get_news(
    response: Response,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Return cached articles without calling NewsAPI or writing to the DB."""
    response.headers["Cache-Control"] = "no-store"
    articles = get_articles(db, limit=limit)
    return {"count": len(articles), "articles": articles}


@router.get("/feed")
def get_feed(
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    try:
        response.headers["Cache-Control"] = "no-store"
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
