"""Kateqoriya modeli (Forex / US / Crypto). Tab filtrləri bununla işləyir."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """Bazar kateqoriyası. `slug` Category enum dəyəri ilə uyğun gəlir."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    # "forex" | "us" | "crypto" — app.core.constants.Category ilə eyni
    slug: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))

    def __repr__(self) -> str:
        return f"<Category {self.slug!r}>"
