from typing import Optional
from sqlalchemy import (
    Boolean,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.model.base import Base


class DBService(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(31), index=True, unique=True)
    url: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(255))
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    apikey_hash: Mapped[bytes] = mapped_column(LargeBinary(64))
    apikey_salt: Mapped[bytes] = mapped_column(LargeBinary(16))

    def update(
        self,
        name: Optional[str] = None,
        url: Optional[str] = None,
        path: Optional[str] = None,
        blocked: Optional[bool] = None,
    ) -> None:
        self.name = name or self.name
        self.url = url or self.url
        self.path = path or self.path
        self.blocked = blocked or self.blocked
