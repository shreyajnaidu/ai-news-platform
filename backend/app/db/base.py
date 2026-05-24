from datetime import datetime
from typing import Annotated

from sqlalchemy import func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

# Base ORM class
class Base(DeclarativeBase):
    pass


# Reusable primary key type
int_pk = Annotated[
    int,
    mapped_column(primary_key=True, autoincrement=True)
]


# Shared model base
class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int_pk]

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )