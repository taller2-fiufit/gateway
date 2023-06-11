from sqlalchemy import (
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.model.base import Base


class DBToken(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sub: Mapped[int] = mapped_column(Integer, index=True)
    iat: Mapped[int] = mapped_column(Integer)
    exp: Mapped[int] = mapped_column(Integer)
