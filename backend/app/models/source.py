"""Xəbər mənbəyi modeli (RSS / API / sayt)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.news import News


class Source(Base, TimestampMixin):
    """Xəbərlərin gəldiyi mənbə. Hər xəbər bir mənbəyə bağlıdır."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    homepage_url: Mapped[str | None] = mapped_column(String(500))
    rss_url: Mapped[str | None] = mapped_column(String(500))
    # Standart kateqoriya (mənbə əsasən bir bazara aiddirsə)
    default_category: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    news: Mapped[list[News]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Source {self.name!r}>"
