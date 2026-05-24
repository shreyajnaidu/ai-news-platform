from app.db.database import engine
from app.db.base import Base

# Import models so SQLAlchemy registers them
from app.models.article import Article


def init_db():
    Base.metadata.create_all(bind=engine)