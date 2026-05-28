"""
app/models/__init__.py
======================
Central import point for all models.

WHY THIS MATTERS:
-----------------
SQLAlchemy needs to "see" every model class BEFORE you call
Base.metadata.create_all(engine). If a model is defined in a file but
never imported, SQLAlchemy doesn't know it exists and won't create its table.

This file solves that problem: by importing every model here, we ensure
they're all registered with Base.metadata. Then in main.py, we just do:

    from app.models import Base  # triggers all model imports
    Base.metadata.create_all(engine)

ADD YOUR MODELS HERE:
---------------------
When you create a new model file (e.g., article.py, user.py), add an
import here:

    from app.models.article import Article
    from app.models.user import User
    from app.models.preference import Preference
"""

from app.db.base import Base
from app.models.article import Article  # noqa: F401 — needed for table creation
from app.models.user import User        # noqa: F401 — needed for table creation

__all__ = ["Base"]
